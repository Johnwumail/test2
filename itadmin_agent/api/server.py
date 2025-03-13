"""
API Server

This module implements the API server for the IT Admin Agent system,
providing endpoints for external systems to interact with the agent.
"""
import logging
import threading
import json
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from utils.logging_setup import get_agent_logger


class TaskRequest(BaseModel):
    """Model for a task request."""
    type: str = Field(..., description="Type of the task")
    description: str = Field(..., description="Description of the task")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the task")
    priority: str = Field(default="medium", description="Priority of the task")


class TaskResponse(BaseModel):
    """Model for a task response."""
    id: str = Field(..., description="ID of the task")
    type: str = Field(..., description="Type of the task")
    description: str = Field(..., description="Description of the task")
    status: str = Field(..., description="Status of the task")
    created_at: str = Field(..., description="Creation timestamp")


class TaskApprovalRequest(BaseModel):
    """Model for a task approval request."""
    approved: bool = Field(..., description="Whether the task is approved")
    comments: Optional[str] = Field(None, description="Comments about the approval decision")


app = FastAPI(title="IT Admin Agent API", version="0.1.0")


def start_api_server(config: Dict[str, Any], orchestrator: Any) -> None:
    """
    Start the API server.
    
    Args:
        config: Configuration dictionary
        orchestrator: Agent Orchestrator instance
    """
    logger = get_agent_logger("api")
    logger.info("Starting API server")
    
    # Store orchestrator in app state
    app.state.orchestrator = orchestrator
    app.state.config = config
    app.state.logger = logger
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config['api'].get('cors_origins', ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Start Uvicorn server in a separate thread
    api_thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={
            "host": config['api'].get('host', "0.0.0.0"),
            "port": config['api'].get('port', 8000),
            "log_level": config['system'].get('log_level', "info").lower(),
        },
        daemon=True
    )
    api_thread.start()
    logger.info(f"API server running at http://{config['api'].get('host', '0.0.0.0')}:{config['api'].get('port', 8000)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "IT Admin Agent API", "version": app.state.config['system']['version']}


@app.get("/health")
async def health():
    """Health check endpoint."""
    orchestrator = app.state.orchestrator
    return {
        "status": "healthy" if orchestrator.is_running else "unhealthy",
        "version": app.state.config['system']['version'],
        "environment": app.state.config['system']['environment']
    }


@app.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest):
    """
    Create a new task.
    
    Args:
        task_request: Task request model
        
    Returns:
        Task response model
    """
    orchestrator = app.state.orchestrator
    logger = app.state.logger
    
    try:
        logger.info(f"API request to create task: {task_request.description}")
        
        # Create the task
        task_id = orchestrator.create_task(
            task_type=task_request.type,
            description=task_request.description,
            parameters=task_request.parameters,
            priority=task_request.priority
        )
        
        # Get the created task
        task = orchestrator.get_task(task_id)
        
        return TaskResponse(
            id=task['id'],
            type=task['type'],
            description=task['description'],
            status=task['status'],
            created_at=task['created_at']
        )
    
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")


@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(status: Optional[str] = None):
    """
    Get all tasks, optionally filtered by status.
    
    Args:
        status: Optional status filter
        
    Returns:
        List of task response models
    """
    orchestrator = app.state.orchestrator
    logger = app.state.logger
    
    try:
        logger.info(f"API request to get tasks {f'with status {status}' if status else ''}")
        
        # Get tasks
        tasks = orchestrator.get_all_tasks(status_filter=status)
        
        # Convert to response models
        task_responses = [
            TaskResponse(
                id=task['id'],
                type=task['type'],
                description=task['description'],
                status=task['status'],
                created_at=task['created_at']
            )
            for task in tasks
        ]
        
        return task_responses
    
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting tasks: {str(e)}")


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """
    Get a task by ID.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Task details
    """
    orchestrator = app.state.orchestrator
    logger = app.state.logger
    
    try:
        logger.info(f"API request to get task {task_id}")
        
        # Get the task
        task = orchestrator.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return task
    
    except KeyError:
        logger.warning(f"Task {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting task: {str(e)}")


@app.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str, approval_request: TaskApprovalRequest):
    """
    Approve or reject a task.
    
    Args:
        task_id: ID of the task
        approval_request: Approval request model
        
    Returns:
        Task details
    """
    orchestrator = app.state.orchestrator
    logger = app.state.logger
    
    try:
        logger.info(f"API request to {'approve' if approval_request.approved else 'reject'} task {task_id}")
        
        # Get the task
        task = orchestrator.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if task['status'] != "waiting_for_approval":
            raise HTTPException(
                status_code=400, 
                detail=f"Task {task_id} is not waiting for approval"
            )
        
        if approval_request.approved:
            # Approve the task
            orchestrator.approve_task(task_id)
            logger.info(f"Task {task_id} approved")
            
            return {"message": f"Task {task_id} approved", "task_id": task_id}
        else:
            # Reject the task
            orchestrator.cancel_task(task_id)
            logger.info(f"Task {task_id} rejected")
            
            return {"message": f"Task {task_id} rejected", "task_id": task_id}
    
    except KeyError:
        logger.warning(f"Task {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    except ValueError as e:
        logger.warning(f"Error approving task {task_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error approving task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error approving task: {str(e)}")


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    Cancel a task.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Task details
    """
    orchestrator = app.state.orchestrator
    logger = app.state.logger
    
    try:
        logger.info(f"API request to cancel task {task_id}")
        
        # Get the task
        task = orchestrator.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Cancel the task
        orchestrator.cancel_task(task_id)
        
        return {"message": f"Task {task_id} cancelled", "task_id": task_id}
    
    except KeyError:
        logger.warning(f"Task {task_id} not found")
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(e)}") 