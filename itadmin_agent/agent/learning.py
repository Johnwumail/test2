"""
Learning Agent

This module implements the Learning Agent which learns from past tasks and experiences.
"""
import logging
import threading
from typing import Dict, Any, List, Optional

from utils.logging_setup import get_agent_logger


class LearningAgent:
    """
    Learning Agent for the IT Admin Agent system.
    
    This class is responsible for:
    - Learning from successful tasks
    - Extracting patterns and reusable components
    - Improving task planning and execution over time
    - Updating the knowledge base with learned information
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Learning Agent.
        
        Args:
            config: Configuration dictionary for the learning agent
        """
        self.logger = get_agent_logger("learning")
        self.logger.info("Initializing Learning Agent")
        
        self.config = config
        self.is_running = False
        self.shutdown_flag = threading.Event()
        
        # Store learning threshold
        self.learning_threshold = self.config.get('learning_threshold', 0.8)
        
        self.logger.info("Learning Agent initialized")
    
    def start(self) -> None:
        """Start the Learning Agent."""
        if self.is_running:
            self.logger.warning("Learning Agent is already running")
            return
        
        self.logger.info("Starting Learning Agent")
        self.shutdown_flag.clear()
        self.is_running = True
        self.logger.info("Learning Agent started")
    
    def stop(self) -> None:
        """Stop the Learning Agent."""
        if not self.is_running:
            self.logger.warning("Learning Agent is not running")
            return
        
        self.logger.info("Stopping Learning Agent")
        self.shutdown_flag.set()
        self.is_running = False
        self.logger.info("Learning Agent stopped")
    
    def learn_from_task(self, task_id: str, task: Dict[str, Any], knowledge_base: Any) -> Dict[str, Any]:
        """
        Learn from a completed task.
        
        Args:
            task_id: ID of the task
            task: Task dictionary
            knowledge_base: Knowledge Base instance
            
        Returns:
            Learning results
        """
        self.logger.info(f"Learning from task {task_id}: {task['description']}")
        
        # Extract successful steps, commands, and scripts
        successful_steps = []
        commands = []
        scripts = []
        
        for step in task.get('steps', []):
            if step.get('status') == 'succeeded':
                successful_steps.append(step)
                
                # Extract command or script if present
                if 'result' in step and 'details' in step['result']:
                    details = step['result']['details']
                    
                    # Extract command
                    if 'command' in details:
                        commands.append({
                            'command': details['command'],
                            'return_code': details.get('return_code'),
                            'stdout': details.get('stdout'),
                            'stderr': details.get('stderr')
                        })
                    
                    # Extract script
                    if 'script_type' in details and 'script' in details:
                        scripts.append({
                            'script_type': details['script_type'],
                            'script': details['script'],
                            'return_code': details.get('return_code'),
                            'stdout': details.get('stdout'),
                            'stderr': details.get('stderr')
                        })
        
        # Determine if the task is worth learning from
        success_ratio = len(successful_steps) / max(1, len(task.get('steps', [])))
        
        if success_ratio >= self.learning_threshold:
            self.logger.info(f"Task {task_id} success ratio {success_ratio} meets learning threshold")
            
            # TODO: Implement actual learning functionality
            # This is a placeholder implementation
            
            # Store learned information in the knowledge base
            knowledge_base.add_task(task)
            
            # If there were useful scripts, store them
            for script in scripts:
                if script.get('script') and script.get('script_type'):
                    knowledge_base.add_script({
                        'name': f"Script from task {task_id}",
                        'description': f"Generated from successful task: {task['description']}",
                        'content': script['script'],
                        'language': script['script_type'],
                        'tags': [task['type']]
                    })
            
            return {
                "status": "success",
                "message": "Successfully learned from task",
                "details": {
                    "success_ratio": success_ratio,
                    "learned_steps": len(successful_steps),
                    "learned_commands": len(commands),
                    "learned_scripts": len(scripts)
                }
            }
        else:
            self.logger.info(f"Task {task_id} success ratio {success_ratio} below learning threshold")
            return {
                "status": "skipped",
                "message": "Task below learning threshold",
                "details": {
                    "success_ratio": success_ratio,
                    "threshold": self.learning_threshold
                }
            }
    
    def execute_step(self, task: Dict[str, Any], step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Execute a learning step.
        
        Args:
            task: Task dictionary
            step: Step dictionary
            step_index: Index of the step
            
        Returns:
            Step execution result
        """
        self.logger.info(f"Executing learning step {step_index} of task {task['id']}: {step['description']}")
        
        # Learning agent typically doesn't execute steps directly
        # This method would only be called for specialized learning tasks
        
        return {
            "status": "success",
            "message": "Learning step executed successfully",
            "details": {
                "learned_patterns": [],
                "recommendations": []
            }
        } 