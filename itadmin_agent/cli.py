#!/usr/bin/env python3
"""
IT Admin Agent CLI

This module provides a command-line interface for interacting with the IT Admin Agent.
"""
import sys
import os
import time
import argparse
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from tabulate import tabulate
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("itadmin-cli")


class ITAdminCLI:
    """Command-line interface for the IT Admin Agent."""
    
    def __init__(self, api_url: str = None):
        """
        Initialize the CLI.
        
        Args:
            api_url: URL of the IT Admin Agent API. If None, uses ITADMIN_API_URL 
                    environment variable or default http://localhost:8000
        """
        self.api_url = api_url or os.environ.get("ITADMIN_API_URL", "http://localhost:8000")
        logger.debug(f"API URL: {self.api_url}")
    
    def check_api_connection(self) -> bool:
        """
        Check if the API is reachable.
        
        Returns:
            True if the API is reachable, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to API: {e}")
            return False
    
    def get_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all tasks, optionally filtered by status.
        
        Args:
            status: Filter tasks by status. If None, all tasks are returned.
            
        Returns:
            List of task dictionaries
        """
        url = f"{self.api_url}/tasks"
        if status:
            url += f"?status={status}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dictionary or None if not found
        """
        try:
            response = requests.get(f"{self.api_url}/tasks/{task_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    def create_task(self, task_type: str, description: str, parameters: Dict[str, Any],
                   priority: str = "medium") -> Optional[str]:
        """
        Create a new task.
        
        Args:
            task_type: Type of the task
            description: Description of the task
            parameters: Task parameters
            priority: Task priority
            
        Returns:
            Task ID if successful, None otherwise
        """
        task_data = {
            "type": task_type,
            "description": description,
            "parameters": parameters,
            "priority": priority
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/tasks",
                json=task_data,
                timeout=30
            )
            response.raise_for_status()
            task = response.json()
            return task.get("id")
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return None
    
    def approve_task(self, task_id: str, approved: bool = True,
                    comments: Optional[str] = None) -> bool:
        """
        Approve or reject a task.
        
        Args:
            task_id: Task ID
            approved: Whether the task is approved
            comments: Optional comments
            
        Returns:
            True if successful, False otherwise
        """
        approval_data = {
            "approved": approved,
            "comments": comments
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/tasks/{task_id}/approve",
                json=approval_data,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to {'approve' if approved else 'reject'} task {task_id}: {e}")
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(f"{self.api_url}/tasks/{task_id}/cancel", timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def wait_for_task(self, task_id: str, poll_interval: int = 5,
                     timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Wait for a task to complete.
        
        Args:
            task_id: Task ID
            poll_interval: How often to check task status (in seconds)
            timeout: Maximum time to wait (in seconds), None for no timeout
            
        Returns:
            Completed task dictionary or None if timeout or error
        """
        start_time = time.time()
        while True:
            task = self.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return None
            
            status = task.get("status")
            if status in ["succeeded", "failed", "cancelled"]:
                return task
            
            if timeout and (time.time() - start_time) > timeout:
                logger.warning(f"Timeout waiting for task {task_id}")
                return None
            
            time.sleep(poll_interval)


def display_task(task: Dict[str, Any], detailed: bool = False) -> None:
    """
    Display a task in a user-friendly format.
    
    Args:
        task: Task dictionary
        detailed: Whether to show detailed information
    """
    status_colors = {
        "pending": Fore.BLUE,
        "planning": Fore.CYAN,
        "executing": Fore.YELLOW,
        "succeeded": Fore.GREEN,
        "failed": Fore.RED,
        "cancelled": Fore.MAGENTA,
        "waiting_for_approval": Fore.BLUE
    }
    
    # Get the color for the status
    status = task.get("status", "unknown")
    color = status_colors.get(status, Fore.WHITE)
    
    # Print task header
    print(f"\n{Fore.WHITE}{Style.BRIGHT}Task ID: {task.get('id')}{Style.RESET_ALL}")
    print(f"Type: {task.get('type')}")
    print(f"Description: {task.get('description')}")
    print(f"Status: {color}{status}{Style.RESET_ALL}")
    print(f"Created: {task.get('created_at')}")
    
    if detailed:
        # Print task parameters
        print(f"\n{Style.BRIGHT}Parameters:{Style.RESET_ALL}")
        if task.get("parameters"):
            for key, value in task.get("parameters", {}).items():
                print(f"  {key}: {value}")
        else:
            print("  No parameters")
        
        # Print task result
        print(f"\n{Style.BRIGHT}Result:{Style.RESET_ALL}")
        if task.get("result"):
            print(f"  {json.dumps(task.get('result'), indent=2)}")
        else:
            print("  No result yet")
        
        # Print task steps
        print(f"\n{Style.BRIGHT}Steps:{Style.RESET_ALL}")
        steps = task.get("steps", [])
        if steps:
            for i, step in enumerate(steps):
                step_status = step.get("status", "pending")
                step_color = status_colors.get(step_status, Fore.WHITE)
                print(f"  {i+1}. {step.get('description')} - "
                      f"{step_color}{step_status}{Style.RESET_ALL}")
        else:
            print("  No steps yet")


def display_task_list(tasks: List[Dict[str, Any]]) -> None:
    """
    Display a list of tasks in a tabulated format.
    
    Args:
        tasks: List of task dictionaries
    """
    if not tasks:
        print(f"{Fore.YELLOW}No tasks found{Style.RESET_ALL}")
        return
    
    status_colors = {
        "pending": Fore.BLUE,
        "planning": Fore.CYAN,
        "executing": Fore.YELLOW,
        "succeeded": Fore.GREEN,
        "failed": Fore.RED,
        "cancelled": Fore.MAGENTA,
        "waiting_for_approval": Fore.BLUE
    }
    
    # Prepare the data for tabulation
    table_data = []
    for task in tasks:
        status = task.get("status", "unknown")
        color = status_colors.get(status, Fore.WHITE)
        colored_status = f"{color}{status}{Style.RESET_ALL}"
        
        table_data.append([
            task.get("id"),
            task.get("type"),
            task.get("description")[:40] + "..." if len(task.get("description", "")) > 40 else task.get("description", ""),
            colored_status,
            task.get("created_at", "")
        ])
    
    # Print the table
    print(tabulate(
        table_data,
        headers=["ID", "Type", "Description", "Status", "Created"],
        tablefmt="simple"
    ))


def load_parameters_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load task parameters from a file.
    
    Args:
        file_path: Path to the parameter file
        
    Returns:
        Dictionary of parameters
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"Parameter file not found: {file_path}")
        return {}
    
    try:
        with open(file_path, 'r') as file:
            if file_path.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(file)
            elif file_path.suffix == '.json':
                return json.load(file)
            else:
                logger.error(f"Unsupported file format: {file_path.suffix}")
                return {}
    except Exception as e:
        logger.error(f"Failed to load parameters from {file_path}: {e}")
        return {}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="IT Admin Agent CLI")
    parser.add_argument(
        "--api-url",
        type=str,
        help="URL of the IT Admin Agent API"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # 'list' command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--status",
        type=str,
        choices=["pending", "planning", "executing", "succeeded", "failed", "cancelled", "waiting_for_approval"],
        help="Filter tasks by status"
    )
    
    # 'get' command
    get_parser = subparsers.add_parser("get", help="Get task details")
    get_parser.add_argument(
        "task_id",
        type=str,
        help="Task ID"
    )
    
    # 'create' command
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument(
        "task_type",
        type=str,
        help="Type of task"
    )
    create_parser.add_argument(
        "description",
        type=str,
        help="Description of the task"
    )
    create_parser.add_argument(
        "--parameters-file",
        type=str,
        help="Path to a JSON or YAML file with task parameters"
    )
    create_parser.add_argument(
        "--parameter", "-p",
        action="append",
        metavar="KEY=VALUE",
        help="Task parameter in the format KEY=VALUE (can be used multiple times)"
    )
    create_parser.add_argument(
        "--priority",
        type=str,
        choices=["low", "medium", "high"],
        default="medium",
        help="Task priority"
    )
    create_parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for the task to complete"
    )
    create_parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout in seconds when waiting"
    )
    
    # 'approve' command
    approve_parser = subparsers.add_parser("approve", help="Approve a task")
    approve_parser.add_argument(
        "task_id",
        type=str,
        help="Task ID"
    )
    approve_parser.add_argument(
        "--reject",
        action="store_true",
        help="Reject instead of approve"
    )
    approve_parser.add_argument(
        "--comments",
        type=str,
        help="Comments about the approval decision"
    )
    
    # 'cancel' command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a task")
    cancel_parser.add_argument(
        "task_id",
        type=str,
        help="Task ID"
    )
    
    # 'wait' command
    wait_parser = subparsers.add_parser("wait", help="Wait for a task to complete")
    wait_parser.add_argument(
        "task_id",
        type=str,
        help="Task ID"
    )
    wait_parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout in seconds"
    )
    wait_parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="How often to check task status (in seconds)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set up logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create CLI instance
    cli = ITAdminCLI(api_url=args.api_url)
    
    # Check API connection
    if not cli.check_api_connection():
        print(f"{Fore.RED}Error: Could not connect to the IT Admin Agent API{Style.RESET_ALL}")
        print(f"Make sure the IT Admin Agent is running and the API URL is correct.")
        print(f"API URL: {cli.api_url}")
        return 1
    
    # Execute command
    if args.command == "list":
        tasks = cli.get_tasks(status=args.status)
        display_task_list(tasks)
        
    elif args.command == "get":
        task = cli.get_task(args.task_id)
        if task:
            display_task(task, detailed=True)
        else:
            print(f"{Fore.RED}Task not found: {args.task_id}{Style.RESET_ALL}")
            return 1
        
    elif args.command == "create":
        # Parse parameters
        parameters = {}
        
        # Load from file if provided
        if args.parameters_file:
            file_parameters = load_parameters_from_file(args.parameters_file)
            parameters.update(file_parameters)
        
        # Add individual parameters
        if args.parameter:
            for param in args.parameter:
                if "=" in param:
                    key, value = param.split("=", 1)
                    # Try to convert to int or float if possible
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            # Keep as string if not a number
                            pass
                    parameters[key] = value
        
        # Create the task
        task_id = cli.create_task(
            task_type=args.task_type,
            description=args.description,
            parameters=parameters,
            priority=args.priority
        )
        
        if task_id:
            print(f"{Fore.GREEN}Task created: {task_id}{Style.RESET_ALL}")
            
            # Wait for the task if requested
            if args.wait:
                print(f"Waiting for task to complete...")
                task = cli.wait_for_task(
                    task_id=task_id,
                    timeout=args.timeout
                )
                
                if task:
                    display_task(task, detailed=True)
                else:
                    print(f"{Fore.YELLOW}Timeout waiting for task{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to create task{Style.RESET_ALL}")
            return 1
        
    elif args.command == "approve":
        success = cli.approve_task(
            task_id=args.task_id,
            approved=not args.reject,
            comments=args.comments
        )
        
        if success:
            action = "rejected" if args.reject else "approved"
            print(f"{Fore.GREEN}Task {args.task_id} {action}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to {'reject' if args.reject else 'approve'} task{Style.RESET_ALL}")
            return 1
        
    elif args.command == "cancel":
        success = cli.cancel_task(args.task_id)
        
        if success:
            print(f"{Fore.GREEN}Task {args.task_id} cancelled{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to cancel task{Style.RESET_ALL}")
            return 1
        
    elif args.command == "wait":
        print(f"Waiting for task {args.task_id} to complete...")
        task = cli.wait_for_task(
            task_id=args.task_id,
            poll_interval=args.poll_interval,
            timeout=args.timeout
        )
        
        if task:
            display_task(task, detailed=True)
        else:
            print(f"{Fore.YELLOW}Timeout or error waiting for task{Style.RESET_ALL}")
            return 1
    
    else:
        print("No command specified. Use --help for usage information.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 