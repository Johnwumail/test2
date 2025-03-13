"""
Agent Orchestrator

This module implements the central orchestrator for coordinating all agent activities.
"""
import logging
import threading
import uuid
from typing import Dict, Any, List, Optional
from enum import Enum

from agent.task_manager import TaskManagerAgent
from agent.diagnostics import DiagnosticsAgent
from agent.execution import ExecutionAgent
from agent.learning import LearningAgent
from agent.validation import ValidationAgent
from utils.logging_setup import get_agent_logger
from knowledge_base.knowledge_base import KnowledgeBase
from task_planner.planner import TaskPlanner


class TaskStatus(Enum):
    """Enum for task status."""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class AgentOrchestrator:
    """
    Central orchestrator for coordinating agent activities.
    
    This class is responsible for:
    - Initializing and managing all agent instances
    - Coordinating task execution across agents
    - Managing the task queue and status
    - Handling human interaction and approvals
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Agent Orchestrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_agent_logger("orchestrator")
        self.logger.info("Initializing Agent Orchestrator")
        
        # Initialize the knowledge base
        self.knowledge_base = KnowledgeBase(config['knowledge_base'])
        
        # Initialize the task planner
        self.task_planner = TaskPlanner(config['task_planner'])
        
        # Initialize agents
        self.agents = {
            'task_manager': TaskManagerAgent(config['agents']['task_manager']),
            'diagnostics': DiagnosticsAgent(config['agents']['diagnostics']),
            'execution': ExecutionAgent(config['agents']['execution']),
            'learning': LearningAgent(config['agents']['learning']),
            'validation': ValidationAgent(config['agents']['validation'])
        }
        
        # Task management
        self.task_lock = threading.RLock()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, threading.Thread] = {}
        
        # Shutdown flag
        self.shutdown_flag = threading.Event()
        self.is_running = False
        
        self.logger.info("Agent Orchestrator initialized")
    
    def start(self) -> None:
        """
        Start the Agent Orchestrator and all agents.
        """
        if self.is_running:
            self.logger.warning("Agent Orchestrator is already running")
            return
        
        self.logger.info("Starting Agent Orchestrator")
        self.shutdown_flag.clear()
        
        # Start all agents
        for agent_name, agent in self.agents.items():
            if self.config['agents'].get(agent_name, {}).get('enabled', True):
                self.logger.info(f"Starting agent: {agent_name}")
                agent.start()
            else:
                self.logger.info(f"Agent {agent_name} is disabled in configuration")
        
        self.is_running = True
        self.logger.info("Agent Orchestrator started")
    
    def stop(self) -> None:
        """
        Stop the Agent Orchestrator and all agents.
        """
        if not self.is_running:
            self.logger.warning("Agent Orchestrator is not running")
            return
            
        self.logger.info("Stopping Agent Orchestrator")
        self.shutdown_flag.set()
        
        # Stop all running tasks
        with self.task_lock:
            for task_id, thread in list(self.active_tasks.items()):
                self.logger.info(f"Stopping task: {task_id}")
                self.cancel_task(task_id)
        
        # Stop all agents
        for agent_name, agent in self.agents.items():
            if agent.is_running:
                self.logger.info(f"Stopping agent: {agent_name}")
                agent.stop()
        
        self.is_running = False
        self.logger.info("Agent Orchestrator stopped")
    
    def create_task(self, task_type: str, description: str, parameters: Dict[str, Any], 
                   priority: str = "medium") -> str:
        """
        Create a new task.
        
        Args:
            task_type: Type of task to create
            description: Human-readable description of the task
            parameters: Parameters for the task
            priority: Priority level (low, medium, high)
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        with self.task_lock:
            self.tasks[task_id] = {
                'id': task_id,
                'type': task_type,
                'description': description,
                'parameters': parameters,
                'priority': priority,
                'status': TaskStatus.PENDING.value,
                'created_at': self._get_timestamp(),
                'updated_at': self._get_timestamp(),
                'steps': [],
                'result': None,
                'error': None
            }
        
        self.logger.info(f"Created task {task_id}: {description}")
        
        # Start task execution in a separate thread
        self._start_task_execution(task_id)
        
        return task_id
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get task details.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task details dictionary
            
        Raises:
            KeyError: If task_id is not found
        """
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            return self.tasks[task_id].copy()
    
    def get_all_tasks(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all tasks, optionally filtered by status.
        
        Args:
            status_filter: Optional filter for task status
            
        Returns:
            List of task dictionaries
        """
        with self.task_lock:
            if status_filter:
                return [task.copy() for task in self.tasks.values() 
                        if task['status'] == status_filter]
            else:
                return [task.copy() for task in self.tasks.values()]
    
    def update_task_status(self, task_id: str, status: str) -> None:
        """
        Update task status.
        
        Args:
            task_id: ID of the task
            status: New status
            
        Raises:
            KeyError: If task_id is not found
            ValueError: If status is invalid
        """
        try:
            # Validate the status
            TaskStatus(status)
        except ValueError:
            raise ValueError(f"Invalid task status: {status}")
        
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            self.tasks[task_id]['status'] = status
            self.tasks[task_id]['updated_at'] = self._get_timestamp()
            
        self.logger.info(f"Updated task {task_id} status to {status}")
    
    def add_task_result(self, task_id: str, result: Any) -> None:
        """
        Add result to a task.
        
        Args:
            task_id: ID of the task
            result: Task result data
            
        Raises:
            KeyError: If task_id is not found
        """
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            self.tasks[task_id]['result'] = result
            self.tasks[task_id]['updated_at'] = self._get_timestamp()
            
        self.logger.info(f"Added result to task {task_id}")
    
    def add_task_error(self, task_id: str, error: str) -> None:
        """
        Add error to a task.
        
        Args:
            task_id: ID of the task
            error: Error message
            
        Raises:
            KeyError: If task_id is not found
        """
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            self.tasks[task_id]['error'] = error
            self.tasks[task_id]['updated_at'] = self._get_timestamp()
            
        self.logger.info(f"Added error to task {task_id}: {error}")
    
    def add_task_step(self, task_id: str, step_description: str, 
                     step_status: str = "pending") -> int:
        """
        Add a step to a task.
        
        Args:
            task_id: ID of the task
            step_description: Description of the step
            step_status: Status of the step
            
        Returns:
            Step index
            
        Raises:
            KeyError: If task_id is not found
        """
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            step = {
                'description': step_description,
                'status': step_status,
                'created_at': self._get_timestamp(),
                'updated_at': self._get_timestamp(),
                'result': None,
                'error': None
            }
            
            self.tasks[task_id]['steps'].append(step)
            self.tasks[task_id]['updated_at'] = self._get_timestamp()
            
            step_index = len(self.tasks[task_id]['steps']) - 1
            
        self.logger.info(f"Added step {step_index} to task {task_id}: {step_description}")
        return step_index
    
    def update_task_step(self, task_id: str, step_index: int, 
                        status: Optional[str] = None, 
                        result: Optional[Any] = None, 
                        error: Optional[str] = None) -> None:
        """
        Update a task step.
        
        Args:
            task_id: ID of the task
            step_index: Index of the step to update
            status: Optional new status
            result: Optional result
            error: Optional error message
            
        Raises:
            KeyError: If task_id is not found
            IndexError: If step_index is out of range
        """
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            if step_index < 0 or step_index >= len(self.tasks[task_id]['steps']):
                raise IndexError(f"Step index {step_index} out of range for task {task_id}")
            
            step = self.tasks[task_id]['steps'][step_index]
            
            if status is not None:
                step['status'] = status
            
            if result is not None:
                step['result'] = result
            
            if error is not None:
                step['error'] = error
            
            step['updated_at'] = self._get_timestamp()
            self.tasks[task_id]['updated_at'] = self._get_timestamp()
            
        self.logger.info(f"Updated step {step_index} of task {task_id}")
    
    def approve_task(self, task_id: str) -> None:
        """
        Approve a task that is waiting for approval.
        
        Args:
            task_id: ID of the task
            
        Raises:
            KeyError: If task_id is not found
            ValueError: If task is not waiting for approval
        """
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            if self.tasks[task_id]['status'] != TaskStatus.WAITING_FOR_APPROVAL.value:
                raise ValueError(f"Task {task_id} is not waiting for approval")
            
            # Resume task execution
            self.update_task_status(task_id, TaskStatus.EXECUTING.value)
            
        self.logger.info(f"Task {task_id} approved")
    
    def cancel_task(self, task_id: str) -> None:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task
            
        Raises:
            KeyError: If task_id is not found
        """
        with self.task_lock:
            if task_id not in self.tasks:
                raise KeyError(f"Task {task_id} not found")
            
            self.update_task_status(task_id, TaskStatus.CANCELLED.value)
            
            # Remove from active tasks if still running
            if task_id in self.active_tasks:
                # The thread will terminate gracefully when it checks the status
                self.logger.info(f"Waiting for task {task_id} to terminate")
                # We don't join the thread here to avoid deadlocks
                # Instead, we remove it from active_tasks
                self.active_tasks.pop(task_id, None)
            
        self.logger.info(f"Task {task_id} cancelled")
    
    def _start_task_execution(self, task_id: str) -> None:
        """
        Start task execution in a separate thread.
        
        Args:
            task_id: ID of the task
        """
        thread = threading.Thread(
            target=self._execute_task, 
            args=(task_id,),
            name=f"task-{task_id}"
        )
        thread.daemon = True
        
        with self.task_lock:
            self.active_tasks[task_id] = thread
            
        thread.start()
        self.logger.info(f"Started execution thread for task {task_id}")
    
    def _execute_task(self, task_id: str) -> None:
        """
        Execute a task.
        
        This method runs in a separate thread for each task.
        
        Args:
            task_id: ID of the task
        """
        try:
            task = self.get_task(task_id)
            self.logger.info(f"Executing task {task_id}: {task['description']}")
            
            # Update task status to planning
            self.update_task_status(task_id, TaskStatus.PLANNING.value)
            
            # Use the task manager agent to plan the task
            task_manager = self.agents['task_manager']
            task_plan = task_manager.plan_task(task, self.knowledge_base, self.task_planner)
            
            # Add task steps based on the plan
            for step in task_plan['steps']:
                self.add_task_step(task_id, step['description'])
            
            # Update task status to executing
            self.update_task_status(task_id, TaskStatus.EXECUTING.value)
            
            # Execute each step
            success = True
            for i, step in enumerate(task_plan['steps']):
                # Check if task was cancelled
                if self.get_task(task_id)['status'] == TaskStatus.CANCELLED.value:
                    self.logger.info(f"Task {task_id} was cancelled, stopping execution")
                    return
                
                self.logger.info(f"Executing step {i} for task {task_id}: {step['description']}")
                
                # Update step status to executing
                self.update_task_step(task_id, i, status="executing")
                
                # Check if human approval is needed
                if step.get('requires_approval', False):
                    self.logger.info(f"Step {i} of task {task_id} requires human approval")
                    self.update_task_status(task_id, TaskStatus.WAITING_FOR_APPROVAL.value)
                    
                    # Wait for approval (or cancellation)
                    while True:
                        current_status = self.get_task(task_id)['status']
                        if current_status == TaskStatus.EXECUTING.value:
                            # Approved, continue
                            break
                        elif current_status == TaskStatus.CANCELLED.value:
                            # Cancelled, stop execution
                            return
                        
                        # Sleep briefly to avoid CPU spin
                        import time
                        time.sleep(0.5)
                
                try:
                    # Determine which agent to use for this step
                    agent_type = step.get('agent_type', 'execution')
                    agent = self.agents[agent_type]
                    
                    # Execute the step
                    step_result = agent.execute_step(task, step, i)
                    
                    # Update step with result
                    self.update_task_step(task_id, i, status="succeeded", result=step_result)
                    
                    # If this is a diagnostic step, update task based on diagnostics
                    if agent_type == 'diagnostics' and step_result.get('diagnosis'):
                        # TODO: Handle diagnostic results
                        pass
                    
                except Exception as e:
                    self.logger.error(f"Error executing step {i} of task {task_id}: {str(e)}", 
                                     exc_info=True)
                    self.update_task_step(task_id, i, status="failed", error=str(e))
                    success = False
                    
                    # Depending on the step's criticality, we might abort the task
                    if step.get('critical', False):
                        self.logger.warning(f"Critical step {i} failed, aborting task {task_id}")
                        break
            
            # Update task status based on execution results
            final_status = TaskStatus.SUCCEEDED.value if success else TaskStatus.FAILED.value
            self.update_task_status(task_id, final_status)
            
            # If task succeeded, send to learning agent
            if success:
                self.logger.info(f"Task {task_id} completed successfully, sending to learning agent")
                learning_agent = self.agents['learning']
                learning_agent.learn_from_task(task_id, self.get_task(task_id), self.knowledge_base)
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {str(e)}", exc_info=True)
            self.add_task_error(task_id, str(e))
            self.update_task_status(task_id, TaskStatus.FAILED.value)
        
        finally:
            # Remove task from active tasks
            with self.task_lock:
                self.active_tasks.pop(task_id, None)
            
            self.logger.info(f"Task {task_id} execution thread completed")
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat() 