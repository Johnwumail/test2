"""
Dashboard

This module implements the web dashboard for the IT Admin Agent system,
providing a user interface for monitoring and controlling the agent.
"""
import os
import logging
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.logging_setup import get_agent_logger


def start_dashboard(config: Dict[str, Any], orchestrator: Any) -> None:
    """
    Start the Streamlit dashboard.
    
    Args:
        config: Configuration dictionary
        orchestrator: Agent Orchestrator instance
    """
    logger = get_agent_logger("dashboard")
    logger.info("Starting dashboard")
    
    # Set environment variables for Streamlit configuration
    os.environ["STREAMLIT_SERVER_PORT"] = str(config.get('dashboard', {}).get('port', 8501))
    os.environ["STREAMLIT_SERVER_ADDRESS"] = config.get('dashboard', {}).get('host', "0.0.0.0")
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    
    # Create a file with the Streamlit dashboard code
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard_app.py")
    
    dashboard_code = '''
import os
import sys
import time
import json
import pickle
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="IT Admin Agent Dashboard",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache for storing data between refreshes
if 'task_cache' not in st.session_state:
    st.session_state.task_cache = {}

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# API URL (This would be configured from the main application)
API_BASE_URL = "http://localhost:8000"

# Helper functions
def get_api_url(endpoint):
    return f"{API_BASE_URL}/{endpoint}"

def api_get(endpoint):
    try:
        response = requests.get(get_api_url(endpoint))
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def api_post(endpoint, data):
    try:
        response = requests.post(get_api_url(endpoint), json=data)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def format_datetime(dt_str):
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str

def get_elapsed_time(start_time_str):
    if not start_time_str:
        return "N/A"
    try:
        start_time = datetime.fromisoformat(start_time_str)
        elapsed = datetime.now() - start_time
        
        # Format as hours:minutes:seconds
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    except:
        return "N/A"

# Sidebar
with st.sidebar:
    st.title("IT Admin Agent")
    
    # Health status
    health = api_get("health")
    if health:
        status_color = "green" if health.get("status") == "healthy" else "red"
        st.markdown(f"<h3>Status: <span style='color:{status_color}'>{health.get('status', 'Unknown')}</span></h3>", unsafe_allow_html=True)
        st.text(f"Version: {health.get('version', 'Unknown')}")
        st.text(f"Environment: {health.get('environment', 'Unknown')}")
    else:
        st.error("Unable to connect to API")
    
    st.divider()
    
    # Navigation
    page = st.radio("Navigation", ["Dashboard", "Tasks", "Create Task"])
    
    # Refresh button
    refresh_col1, refresh_col2 = st.columns([3, 1])
    with refresh_col1:
        st.text(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    with refresh_col2:
        if st.button("🔄"):
            st.session_state.last_refresh = datetime.now()
            st.experimental_rerun()
    
    # Auto refresh
    auto_refresh = st.checkbox("Auto refresh", value=True)
    if auto_refresh:
        refresh_interval = st.slider("Refresh interval (sec)", 5, 60, 10)
        
        # Check if it's time to refresh
        if (datetime.now() - st.session_state.last_refresh).total_seconds() > refresh_interval:
            st.session_state.last_refresh = datetime.now()
            st.experimental_rerun()

# Main content
if page == "Dashboard":
    st.title("IT Admin Agent Dashboard")
    
    # Get tasks for the dashboard
    tasks = api_get("tasks")
    
    if tasks:
        # Create metrics for task counts
        col1, col2, col3, col4 = st.columns(4)
        
        pending_count = sum(1 for task in tasks if task.get("status") in ["pending", "planning"])
        running_count = sum(1 for task in tasks if task.get("status") in ["executing", "waiting_for_approval"])
        success_count = sum(1 for task in tasks if task.get("status") == "succeeded")
        failed_count = sum(1 for task in tasks if task.get("status") in ["failed", "cancelled"])
        
        col1.metric("Pending", pending_count)
        col2.metric("Running", running_count)
        col3.metric("Succeeded", success_count)
        col4.metric("Failed", failed_count)
        
        # Charts section
        st.subheader("Task Status Overview")
        
        # Task status distribution
        status_counts = {}
        for task in tasks:
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig1 = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="Task Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Safe,
            hole=0.4
        )
        st.plotly_chart(fig1)
        
        # Recent activity
        st.subheader("Recent Activity")
        
        # Sort tasks by created_at, most recent first
        sorted_tasks = sorted(tasks, key=lambda t: t.get("created_at", ""), reverse=True)
        recent_tasks = sorted_tasks[:5]
        
        if recent_tasks:
            for task in recent_tasks:
                task_id = task.get("id")
                description = task.get("description")
                status = task.get("status")
                created_at = format_datetime(task.get("created_at"))
                
                status_color = {
                    "pending": "blue",
                    "planning": "blue",
                    "executing": "orange",
                    "waiting_for_approval": "purple",
                    "succeeded": "green",
                    "failed": "red",
                    "cancelled": "gray"
                }.get(status, "black")
                
                st.markdown(f"""
                <div style="border-left: 4px solid {status_color}; padding-left: 10px; margin-bottom: 10px;">
                    <strong>{description}</strong> 
                    <span style="color: {status_color}">({status})</span><br/>
                    <small>ID: {task_id}<br/>Created: {created_at}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent tasks")
    else:
        st.warning("No tasks available or unable to connect to API")

elif page == "Tasks":
    st.title("Task Management")
    
    # Create tabs for different task views
    tab1, tab2, tab3, tab4 = st.tabs(["Active", "Pending Approval", "Completed", "All Tasks"])
    
    # Get all tasks
    tasks = api_get("tasks")
    
    if tasks:
        # Active tasks
        with tab1:
            active_tasks = [t for t in tasks if t.get("status") in ["executing", "planning"]]
            if active_tasks:
                for task in active_tasks:
                    task_id = task.get("id")
                    
                    # Get full task details
                    task_details = api_get(f"tasks/{task_id}")
                    
                    if task_details:
                        with st.expander(f"{task_details.get('description')} ({task_details.get('status')})"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**ID:** {task_id}")
                                st.markdown(f"**Type:** {task_details.get('type')}")
                                st.markdown(f"**Status:** {task_details.get('status')}")
                                st.markdown(f"**Created:** {format_datetime(task_details.get('created_at'))}")
                                st.markdown(f"**Elapsed:** {get_elapsed_time(task_details.get('created_at'))}")
                            
                            with col2:
                                if task_details.get("status") != "cancelled":
                                    if st.button("Cancel", key=f"cancel_{task_id}"):
                                        if api_post(f"tasks/{task_id}/cancel", {}):
                                            st.success(f"Task {task_id} cancelled")
                                            time.sleep(1)
                                            st.experimental_rerun()
                            
                            # Show steps if any
                            steps = task_details.get("steps", [])
                            if steps:
                                st.subheader("Steps")
                                for i, step in enumerate(steps):
                                    step_status = step.get("status", "unknown")
                                    status_emoji = {
                                        "pending": "⏳",
                                        "executing": "🔄",
                                        "succeeded": "✅",
                                        "failed": "❌",
                                    }.get(step_status, "⚪")
                                    
                                    st.markdown(f"{status_emoji} **Step {i+1}:** {step.get('description')}")
                            
                            # Show parameters
                            with st.expander("Parameters"):
                                st.json(task_details.get("parameters", {}))
            else:
                st.info("No active tasks")
        
        # Tasks waiting for approval
        with tab2:
            approval_tasks = [t for t in tasks if t.get("status") == "waiting_for_approval"]
            if approval_tasks:
                for task in approval_tasks:
                    task_id = task.get("id")
                    
                    # Get full task details
                    task_details = api_get(f"tasks/{task_id}")
                    
                    if task_details:
                        with st.expander(f"{task_details.get('description')} (Needs Approval)", expanded=True):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.markdown(f"**ID:** {task_id}")
                                st.markdown(f"**Type:** {task_details.get('type')}")
                                st.markdown(f"**Created:** {format_datetime(task_details.get('created_at'))}")
                            
                            with col2:
                                if st.button("Approve", key=f"approve_{task_id}", type="primary"):
                                    if api_post(f"tasks/{task_id}/approve", {"approved": True}):
                                        st.success(f"Task {task_id} approved")
                                        time.sleep(1)
                                        st.experimental_rerun()
                            
                            with col3:
                                if st.button("Reject", key=f"reject_{task_id}"):
                                    if api_post(f"tasks/{task_id}/approve", {"approved": False}):
                                        st.success(f"Task {task_id} rejected")
                                        time.sleep(1)
                                        st.experimental_rerun()
                            
                            # Show steps if any
                            steps = task_details.get("steps", [])
                            if steps:
                                st.subheader("Steps")
                                for i, step in enumerate(steps):
                                    step_status = step.get("status", "unknown")
                                    status_emoji = {
                                        "pending": "⏳",
                                        "executing": "🔄",
                                        "succeeded": "✅",
                                        "failed": "❌",
                                    }.get(step_status, "⚪")
                                    
                                    st.markdown(f"{status_emoji} **Step {i+1}:** {step.get('description')}")
                            
                            # Show parameters
                            with st.expander("Parameters"):
                                st.json(task_details.get("parameters", {}))
            else:
                st.info("No tasks waiting for approval")
        
        # Completed tasks
        with tab3:
            completed_tasks = [t for t in tasks if t.get("status") in ["succeeded", "failed", "cancelled"]]
            if completed_tasks:
                # Sort by created_at, newest first
                completed_tasks = sorted(completed_tasks, key=lambda t: t.get("created_at", ""), reverse=True)
                
                # Convert to DataFrame for table display
                task_data = []
                for task in completed_tasks:
                    task_data.append({
                        "ID": task.get("id"),
                        "Description": task.get("description"),
                        "Type": task.get("type"),
                        "Status": task.get("status"),
                        "Created": format_datetime(task.get("created_at")),
                    })
                
                # Display table with tasks
                df = pd.DataFrame(task_data)
                st.dataframe(df, use_container_width=True)
                
                # Create detailed view for the selected task
                if task_data:
                    task_ids = df['ID'].tolist()
                    selected_task_id = st.selectbox("Select task for details", task_ids)
                    
                    if selected_task_id:
                        task_details = api_get(f"tasks/{selected_task_id}")
                        
                        if task_details:
                            st.subheader("Task Details")
                            st.markdown(f"**Description:** {task_details.get('description')}")
                            st.markdown(f"**Status:** {task_details.get('status')}")
                            st.markdown(f"**Created:** {format_datetime(task_details.get('created_at'))}")
                            
                            # Show steps if any
                            steps = task_details.get("steps", [])
                            if steps:
                                st.subheader("Steps")
                                for i, step in enumerate(steps):
                                    step_status = step.get("status", "unknown")
                                    status_emoji = {
                                        "pending": "⏳",
                                        "executing": "🔄",
                                        "succeeded": "✅",
                                        "failed": "❌",
                                    }.get(step_status, "⚪")
                                    
                                    st.markdown(f"{status_emoji} **Step {i+1}:** {step.get('description')}")
                                    
                                    # Show result or error if available
                                    if step.get("result"):
                                        with st.expander("Result"):
                                            st.json(step.get("result"))
                                    
                                    if step.get("error"):
                                        st.error(step.get("error"))
                            
                            # Show result if available
                            if task_details.get("result"):
                                st.subheader("Task Result")
                                st.json(task_details.get("result"))
                            
                            # Show error if available
                            if task_details.get("error"):
                                st.subheader("Task Error")
                                st.error(task_details.get("error"))
            else:
                st.info("No completed tasks")
        
        # All tasks
        with tab4:
            if tasks:
                # Sort by created_at, newest first
                sorted_tasks = sorted(tasks, key=lambda t: t.get("created_at", ""), reverse=True)
                
                # Convert to DataFrame for table display
                task_data = []
                for task in sorted_tasks:
                    task_data.append({
                        "ID": task.get("id"),
                        "Description": task.get("description"),
                        "Type": task.get("type"),
                        "Status": task.get("status"),
                        "Created": format_datetime(task.get("created_at")),
                    })
                
                # Display table with tasks
                df = pd.DataFrame(task_data)
                st.dataframe(df, use_container_width=True)
    else:
        st.warning("No tasks available or unable to connect to API")

elif page == "Create Task":
    st.title("Create New Task")
    
    # Task creation form
    with st.form("create_task_form"):
        # Task type
        task_type = st.selectbox(
            "Task Type",
            [
                "server_provision",
                "server_configure",
                "package_install",
                "service_manage",
                "backup_restore",
                "security_scan",
                "network_configure",
                "database_manage",
                "file_manage",
                "user_manage",
                "diagnostics",
                "other"
            ]
        )
        
        # Task description
        task_description = st.text_input("Task Description", placeholder="Describe what you want the agent to do")
        
        # Task priority
        task_priority = st.select_slider(
            "Priority",
            options=["low", "medium", "high"],
            value="medium"
        )
        
        # Task parameters (depends on the task type)
        st.subheader("Parameters")
        
        # For server provision or configure
        if task_type in ["server_provision", "server_configure"]:
            hostname = st.text_input("Hostname")
            ip_address = st.text_input("IP Address")
            os_type = st.selectbox("OS Type", ["ubuntu", "centos", "debian", "windows", "other"])
            os_version = st.text_input("OS Version")
            
            parameters = {
                "hostname": hostname,
                "ip_address": ip_address,
                "os_type": os_type,
                "os_version": os_version
            }
        
        # For package install
        elif task_type == "package_install":
            server = st.text_input("Server")
            packages = st.text_area("Packages (one per line)")
            package_manager = st.selectbox("Package Manager", ["apt", "yum", "dnf", "brew", "pip", "npm", "other"])
            
            parameters = {
                "server": server,
                "packages": [pkg.strip() for pkg in packages.split("\\n") if pkg.strip()],
                "package_manager": package_manager
            }
        
        # For service management
        elif task_type == "service_manage":
            server = st.text_input("Server")
            service = st.text_input("Service Name")
            action = st.selectbox("Action", ["start", "stop", "restart", "enable", "disable", "status"])
            
            parameters = {
                "server": server,
                "service": service,
                "action": action
            }
        
        # For other task types
        else:
            # Generic parameters as JSON
            parameters_json = st.text_area(
                "Parameters (JSON format)",
                value="{}",
                help="Enter parameters as JSON object"
            )
            
            try:
                parameters = json.loads(parameters_json)
            except:
                st.error("Invalid JSON format")
                parameters = {}
        
        # Submit button
        submit_button = st.form_submit_button("Create Task")
    
    # Handle form submission
    if submit_button:
        if not task_description:
            st.error("Task description is required")
        else:
            # Create task request
            task_request = {
                "type": task_type,
                "description": task_description,
                "parameters": parameters,
                "priority": task_priority
            }
            
            # Submit task
            result = api_post("tasks", task_request)
            
            if result:
                st.success(f"Task created successfully: {result.get('id')}")
                
                # Show created task details
                st.json(result)
                
                # Provide a button to view the task
                if st.button("View Task"):
                    # Switch to Tasks page
                    st.session_state.page = "Tasks"
                    st.experimental_rerun()
            else:
                st.error("Failed to create task")

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center;'><small>IT Admin Agent Dashboard • &copy; 2023</small></div>", unsafe_allow_html=True)
'''
    
    with open(dashboard_path, "w") as f:
        f.write(dashboard_code)
    
    # Start Streamlit in a separate process
    import subprocess
    dashboard_process = subprocess.Popen(
        ["streamlit", "run", dashboard_path, "--server.headless=true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    logger.info(f"Dashboard started at http://{config.get('dashboard', {}).get('host', '0.0.0.0')}:{config.get('dashboard', {}).get('port', 8501)}")
    
    # Return the process object so it can be terminated when the orchestrator stops
    return dashboard_process 