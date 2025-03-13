"""
Task Manager Agent

This module implements the Task Manager Agent which is responsible for planning tasks
and coordinating their execution.
"""
import logging
import threading
from typing import Dict, Any, List, Optional

from utils.logging_setup import get_agent_logger


class TaskManagerAgent:
    """
    Task Manager Agent for the IT Admin Agent system.
    
    This class is responsible for:
    - Planning task execution
    - Breaking complex tasks into steps
    - Determining agent assignments for each step
    - Coordinating execution across agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Task Manager Agent.
        
        Args:
            config: Configuration dictionary for the task manager
        """
        self.logger = get_agent_logger("task_manager")
        self.logger.info("Initializing Task Manager Agent")
        
        self.config = config
        self.is_running = False
        self.shutdown_flag = threading.Event()
        
        # Store task plans
        self.task_plans: Dict[str, Dict[str, Any]] = {}
        self.task_plans_lock = threading.RLock()
        
        self.logger.info("Task Manager Agent initialized")
    
    def start(self) -> None:
        """Start the Task Manager Agent."""
        if self.is_running:
            self.logger.warning("Task Manager Agent is already running")
            return
        
        self.logger.info("Starting Task Manager Agent")
        self.shutdown_flag.clear()
        self.is_running = True
        self.logger.info("Task Manager Agent started")
    
    def stop(self) -> None:
        """Stop the Task Manager Agent."""
        if not self.is_running:
            self.logger.warning("Task Manager Agent is not running")
            return
        
        self.logger.info("Stopping Task Manager Agent")
        self.shutdown_flag.set()
        self.is_running = False
        self.logger.info("Task Manager Agent stopped")
    
    def plan_task(self, task: Dict[str, Any], knowledge_base: Any, task_planner: Any) -> Dict[str, Any]:
        """
        Plan a task using the task planner and knowledge base.
        
        Args:
            task: Task dictionary
            knowledge_base: Knowledge Base instance
            task_planner: Task Planner instance
            
        Returns:
            Task plan dictionary
        """
        self.logger.info(f"Planning task {task['id']}: {task['description']}")
        
        # Check for similar tasks in the knowledge base
        similar_tasks = knowledge_base.search_similar_tasks(task['description'])
        
        # Determine whether to reuse a previous plan
        reuse_plan = False
        similar_task_id = None
        
        if similar_tasks and self.config.get('reuse_similar_plans', True):
            # Find the most similar, successful task of the same type
            for similar_task in similar_tasks:
                if (similar_task['type'] == task['type'] and 
                    similar_task['status'] == 'succeeded' and
                    self._parameter_similarity(task['parameters'], similar_task['parameters']) > 0.8):
                    reuse_plan = True
                    similar_task_id = similar_task['id']
                    self.logger.info(f"Found similar successful task: {similar_task_id}")
                    break
        
        if reuse_plan and similar_task_id:
            # Retrieve the full similar task
            similar_task = knowledge_base.get_task(similar_task_id)
            
            # Create a plan based on the similar task
            plan = self._create_plan_from_similar_task(task, similar_task)
            self.logger.info(f"Created plan for task {task['id']} based on similar task {similar_task_id}")
        else:
            # Create a new plan using the task planner
            plan = task_planner.create_plan(task)
            self.logger.info(f"Created new plan for task {task['id']}")
        
        # Store the plan
        with self.task_plans_lock:
            self.task_plans[task['id']] = plan
        
        return plan
    
    def _create_plan_from_similar_task(self, current_task: Dict[str, Any], 
                                      similar_task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a task plan based on a similar task.
        
        Args:
            current_task: Current task dictionary
            similar_task: Similar task dictionary
            
        Returns:
            Task plan dictionary
        """
        # Extract steps from the similar task
        steps = []
        
        for i, step in enumerate(similar_task.get('steps', [])):
            # Only include steps that were successful
            if step.get('status') == 'succeeded':
                steps.append({
                    'description': step['description'],
                    'agent_type': step.get('agent_type', 'execution'),
                    'requires_approval': True if i == 0 else False,  # Require approval for first step
                    'critical': i == 0,  # First step is critical
                    'parameters': {}  # We don't have original parameters, will need to be filled
                })
        
        # Create the plan
        plan = {
            'task_id': current_task['id'],
            'summary': f"Plan for {current_task['type']} based on similar task {similar_task['id']}",
            'steps': steps
        }
        
        return plan
    
    def _parameter_similarity(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """
        Calculate parameter similarity between two tasks.
        
        This is a simple implementation that checks for key overlap and value equality.
        A more sophisticated implementation could use semantic similarity.
        
        Args:
            params1: First parameter dictionary
            params2: Second parameter dictionary
            
        Returns:
            Similarity score between 0 and 1
        """
        if not params1 and not params2:
            return 1.0
        
        if not params1 or not params2:
            return 0.0
        
        # Get keys from both parameter sets
        keys1 = set(params1.keys())
        keys2 = set(params2.keys())
        
        # Calculate key overlap
        shared_keys = keys1.intersection(keys2)
        all_keys = keys1.union(keys2)
        
        if not shared_keys:
            return 0.0
        
        # Calculate value similarity for shared keys
        value_matches = 0
        for key in shared_keys:
            if params1[key] == params2[key]:
                value_matches += 1
        
        # Calculate overall similarity
        key_similarity = len(shared_keys) / len(all_keys)
        value_similarity = value_matches / len(shared_keys) if shared_keys else 0
        
        # Weighted combination
        return 0.6 * key_similarity + 0.4 * value_similarity
    
    def get_plan(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the plan for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task plan or None if not found
        """
        with self.task_plans_lock:
            return self.task_plans.get(task_id)
    
    def update_plan(self, task_id: str, updated_plan: Dict[str, Any]) -> None:
        """
        Update the plan for a task.
        
        Args:
            task_id: Task ID
            updated_plan: Updated task plan
        """
        with self.task_plans_lock:
            self.task_plans[task_id] = updated_plan
        
        self.logger.info(f"Updated plan for task {task_id}")
    
    def execute_step(self, task: Dict[str, Any], step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Execute a step of a task.
        
        This method is called by the orchestrator for steps assigned to the task manager.
        
        Args:
            task: Task dictionary
            step: Step dictionary
            step_index: Index of the step
            
        Returns:
            Step execution result
        """
        self.logger.info(f"Executing step {step_index} of task {task['id']}: {step['description']}")
        
        # Task manager typically doesn't execute steps directly
        # It would coordinate other agents to execute steps
        # Here we just return a success result
        
        return {
            "status": "success",
            "message": "Task manager coordinated step execution",
            "details": None
        } 