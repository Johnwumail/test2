"""
Task Planner

This module implements the task planning capabilities for the IT Admin Agent system.
It uses LLMs to generate plans for tasks based on task descriptions and parameters.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

import openai
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from utils.logging_setup import get_agent_logger


class TaskStep(BaseModel):
    """Model for a task step."""
    description: str = Field(description="Human-readable description of the step")
    agent_type: str = Field(description="Type of agent to execute this step (execution, diagnostics, etc.)")
    requires_approval: bool = Field(
        description="Whether this step requires human approval before execution"
    )
    critical: bool = Field(
        description="Whether this step is critical for task success (failure aborts task)"
    )
    parameters: Dict[str, Any] = Field(
        description="Parameters for the step execution", default_factory=dict
    )


class TaskPlan(BaseModel):
    """Model for a task plan."""
    task_id: str = Field(description="ID of the task")
    summary: str = Field(description="Summary of the task plan")
    steps: List[TaskStep] = Field(description="Ordered list of steps to execute")


class TaskPlanner:
    """
    Task Planner for the IT Admin Agent system.
    
    This class is responsible for:
    - Generating plans for tasks
    - Breaking down complex tasks into manageable steps
    - Identifying required approvals and dependencies
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Task Planner.
        
        Args:
            config: Configuration dictionary for the task planner
        """
        self.logger = get_agent_logger("task_planner")
        self.logger.info("Initializing Task Planner")
        
        self.config = config
        
        # Initialize OpenAI client
        openai.api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Define the task planning prompt template
        self.planning_prompt = PromptTemplate(
            template="""
You are an expert IT systems administrator tasked with planning complex datacenter operations.
Your job is to break down the following task into clear, actionable steps.

TASK TYPE: {task_type}
TASK DESCRIPTION: {task_description}
TASK PARAMETERS: {task_parameters}

For each step, consider:
1. Which agent should execute it (execution, diagnostics, validation, etc.)
2. Whether human approval is required before execution
3. Whether the step is critical (failure should abort the entire task)
4. What parameters are needed for execution

Think step by step, ensuring:
- Steps are in logical sequence
- Dependencies between steps are accounted for
- High-risk operations are flagged for approval
- Proper validation and error checking are included

Provide your response in the following format:

{format_instructions}
""",
            input_variables=["task_type", "task_description", "task_parameters"],
            partial_variables={
                "format_instructions": PydanticOutputParser(pydantic_object=TaskPlan).get_format_instructions()
            }
        )
        
        # Initialize LLM
        self.llm = OpenAI(
            model_name=self.config['llm']['model'],
            temperature=self.config['llm']['temperature'],
            max_tokens=self.config['llm']['max_tokens']
        )
        
        # Initialize LLM Chain
        self.planning_chain = LLMChain(
            llm=self.llm,
            prompt=self.planning_prompt
        )
        
        self.logger.info("Task Planner initialization complete")
    
    def create_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a plan for a task.
        
        Args:
            task: Task dictionary
            
        Returns:
            Plan dictionary
        """
        self.logger.info(f"Creating plan for task: {task['id']}")
        
        try:
            # Prepare inputs for the prompt
            inputs = {
                "task_type": task['type'],
                "task_description": task['description'],
                "task_parameters": json.dumps(task['parameters'])
            }
            
            # Generate the plan using the LLM
            plan_text = self.planning_chain.run(inputs)
            
            # Parse the plan from the LLM output
            parser = PydanticOutputParser(pydantic_object=TaskPlan)
            plan = parser.parse(plan_text)
            
            # Convert to dictionary
            plan_dict = plan.dict()
            plan_dict['task_id'] = task['id']
            
            # Apply default checks if configured
            if self.config.get('default_checks'):
                self._add_default_checks(plan_dict)
            
            self.logger.info(f"Plan created for task {task['id']} with {len(plan_dict['steps'])} steps")
            
            return plan_dict
        
        except Exception as e:
            self.logger.error(f"Error creating plan for task {task['id']}: {str(e)}", exc_info=True)
            
            # Create a basic fallback plan
            fallback_plan = {
                "task_id": task['id'],
                "summary": f"Basic plan for {task['type']} (fallback due to planning error)",
                "steps": [
                    {
                        "description": f"Execute {task['type']} operation",
                        "agent_type": "execution",
                        "requires_approval": True,
                        "critical": True,
                        "parameters": task['parameters']
                    },
                    {
                        "description": f"Verify {task['type']} operation result",
                        "agent_type": "validation",
                        "requires_approval": False,
                        "critical": False,
                        "parameters": {}
                    }
                ]
            }
            
            self.logger.warning(f"Using fallback plan for task {task['id']}")
            return fallback_plan
    
    def _add_default_checks(self, plan: Dict[str, Any]) -> None:
        """
        Add default checks to a plan based on configuration.
        
        Args:
            plan: Plan dictionary to modify
        """
        default_checks = self.config['default_checks']
        
        # Add syntax validation if configured
        if 'syntax_validation' in default_checks:
            plan['steps'].append({
                "description": "Perform syntax validation on executed commands",
                "agent_type": "validation",
                "requires_approval": False,
                "critical": False,
                "parameters": {"type": "syntax"}
            })
        
        # Add security scan if configured
        if 'security_scan' in default_checks:
            plan['steps'].append({
                "description": "Perform security scan on changes",
                "agent_type": "validation",
                "requires_approval": False,
                "critical": True,
                "parameters": {"type": "security"}
            })
        
        # Add impact assessment if configured
        if 'impact_assessment' in default_checks:
            plan['steps'].append({
                "description": "Assess impact of changes",
                "agent_type": "diagnostics",
                "requires_approval": False,
                "critical": False,
                "parameters": {"type": "impact"}
            })
    
    def refine_plan(self, task: Dict[str, Any], plan: Dict[str, Any], 
                   feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine a plan based on feedback.
        
        Args:
            task: Task dictionary
            plan: Original plan dictionary
            feedback: Feedback dictionary
            
        Returns:
            Updated plan dictionary
        """
        self.logger.info(f"Refining plan for task {task['id']} based on feedback")
        
        # TODO: Implement plan refinement based on feedback
        # This would typically use the LLM to modify the plan
        
        # For now, just return the original plan
        return plan 