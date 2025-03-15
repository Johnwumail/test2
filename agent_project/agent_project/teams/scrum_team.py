"""
Scrum team implementation using SelectorGroupChat.
"""

from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage

from agent_project.models.clients import gemini_model_client
from agent_project.agents.dev_agents import (
    python_dev_agent, 
    code_reviewer_agent, 
    scrum_master_agent, 
    product_owner_agent, 
    qa_engineer_agent
)


class ScrumTeam:
    """
    A Scrum team implemented using SelectorGroupChat for dynamic team interactions.
    The team includes:
    - Python Developer: Writes code
    - Code Reviewer: Reviews code for quality and standards
    - Scrum Master: Facilitates the process and provides guidance 
    - Product Owner: Defines requirements and priorities
    - QA Engineer: Tests and validates code
    """
    
    def __init__(self, selector_prompt=None, allow_repeat_speaker=False):
        """
        Initialize the Scrum team.
        
        Args:
            selector_prompt (str, optional): Custom prompt for the selection model.
            allow_repeat_speaker (bool): Whether to allow the same agent to speak consecutively.
        """
        # Define all team members
        self.team_members = [
            product_owner_agent,
            python_dev_agent,
            code_reviewer_agent,
            qa_engineer_agent
        ]
        
        # Define termination condition
        self.termination = TextMentionTermination("TERMINATE")
        
        # Create custom selector prompt if not provided
        if selector_prompt is None:
            selector_prompt = """
            You are a team coordinator. Your task is to select the next team member who should speak based on the conversation context.
            
            Team members:
            - python_developer: Expert Python developer who writes clean, efficient code
            - code_reviewer: Code quality expert who reviews for bugs, style, and performance
            - product_owner: Defines requirements and prioritizes features
            - qa_engineer: Tests code and identifies potential issues
            
            Workflow:
            - product_owner get the task from the user and define the requirements, when the task is defined, the product_owner will pass the task to the python_developer
            - python_developer write the code based on the task and the requirements, when the code is written, the python_developer will pass the code to the code_reviewer
            - code_reviewer review the code, if the code is not good, the code_reviewer will pass the code to the python_developer to improve the code, if the code is good, the code_reviewer will pass the code to the qa_engineer
            - qa_engineer test the code, if the code is not good, the qa_engineer will pass the code to the python_developer to improve the code, if the code is good, the qa_engineer will pass the code to the product_owner to final check
            - product_owner final check the code and test result, return the result to the user
            
            Based on the conversation, who should speak next to move the task forward most effectively?
            Be strategic about your choice - select the team member whose expertise is most needed at this point in the discussion.
            """
        
        # Create the SelectorGroupChat team
        # Note: We're not passing allow_repeat_speaker as it might not be supported in this version
        self.team = SelectorGroupChat(
            participants=self.team_members,
            model_client=gemini_model_client,
            termination_condition=self.termination,
            selector_prompt=selector_prompt
        )

        self.team = RoundRobinGroupChat(
            participants=self.team_members,
            # model_client=gemini_model_client,
            termination_condition=self.termination,
            # selector_prompt=selector_prompt
        )
        
        # Store the allow_repeat_speaker preference for future reference
        self.allow_repeat_speaker = allow_repeat_speaker
    
    async def run(self, task):
        """
        Run the Scrum team on a given task.
        
        Args:
            task (str): The task or user story to be implemented.
            
        Returns:
            The result of the team's work.
        """
        return await self.team.run(task=task)
    
    async def run_with_console(self, task):
        """
        Run the Scrum team and display the conversation in the console.
        
        Args:
            task (str): The task or user story to be implemented.
        """
        print("🏃‍♂️ Starting Scrum Team Workflow with Dynamic Speaker Selection")
        print(f"📋 Task: {task}")
        print("\n💬 Team discussion will start now. All team members, including the Scrum Master, are AI agents.")
        
        # Start the team run with streaming to console
        await Console(
            self.team.run_stream(task=task),
            output_stats=True
        )
        
        print("\n✅ Development workflow completed!")
    
    def reset(self):
        """
        Reset the team's conversation history.
        """
        self.team.reset()


async def use_scrum_team(task, enable_repeat_speaker=False):
    """
    Use the Scrum team to complete a development task.
    
    Args:
        task (str): The development task or user story.
        enable_repeat_speaker (bool): Whether to allow agents to speak consecutively.
    """
    # Create a new Scrum team instance
    scrum_team = ScrumTeam(allow_repeat_speaker=enable_repeat_speaker)
    
    # Run the team with console output
    await scrum_team.run_with_console(task)


# Example tasks
EXAMPLE_TASKS = [
    "We need a Python function that validates email addresses using regular expressions",
    "Create a data processing function that reads a CSV file, calculates statistics, and generates a report",
    "Implement a secure password hashing utility with salt"
]


if __name__ == "__main__":
    import asyncio
    
    # Run the Scrum team on the first example task
    asyncio.run(use_scrum_team(EXAMPLE_TASKS[0])) 