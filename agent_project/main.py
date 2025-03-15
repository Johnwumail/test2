#!/usr/bin/env python
"""
Agent Project - Entry Point Script

This script provides a command-line entry point for easily using various features in the project.
It allows users to choose different workflows and interaction methods.
"""

import asyncio
import argparse
from agent_project import (
    use_scrum_team,
    agile_development_workflow,
    use_python_dev_agent_streaming,
    use_code_reviewer_agent,
    develop_and_review
)

import logging

from autogen_core import TRACE_LOGGER_NAME

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Define example tasks
EXAMPLE_TASKS = [
    "Create a Python function to validate email addresses",
    "Implement a secure password hashing tool with salt functionality",
    "Write a data processing function that reads a CSV file, calculates statistics, and generates a report"
]


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="AutoGen Scrum Team")
    
    # Workflow selection
    parser.add_argument(
        "--workflow", "-w",
        choices=["scrum", "agile", "dev", "review", "dev_review"],
        default="scrum",
        help="Select workflow type: scrum=Full Scrum Team, agile=Round Robin workflow, dev=Developer only, review=Code review, dev_review=Development+Review"
    )
    
    # Task specification
    task_group = parser.add_mutually_exclusive_group()
    task_group.add_argument(
        "--task", "-t",
        type=str,
        help="Custom task to execute"
    )
    task_group.add_argument(
        "--example", "-e",
        type=int,
        choices=[1, 2, 3],
        help="Use example task (1-3)"
    )
    
    # Code review options
    parser.add_argument(
        "--code", "-c",
        type=str,
        help="Code to review (only for review workflow)"
    )
    
    # Additional options
    parser.add_argument(
        "--repeat-speaker",
        action="store_true",
        help="Allow the same agent to speak consecutively (only applies to scrum workflow)"
    )
    
    return parser.parse_args()


async def main():
    """Main function, run the appropriate workflow based on command line arguments"""
    args = parse_args()
    
    # Determine task
    task = None
    if args.task:
        task = args.task
    elif args.example:
        task = EXAMPLE_TASKS[args.example - 1]
    elif args.workflow != "review":  # Review workflow doesn't need a task
        # If no task or example is specified, use the first example
        task = EXAMPLE_TASKS[0]
    
    # Run the appropriate functionality based on the selected workflow
    if args.workflow == "scrum":
        if not task:
            print("Error: scrum workflow requires a task. Use --task or --example to specify a task.")
            return
        await use_scrum_team(task, enable_repeat_speaker=args.repeat_speaker)
    
    elif args.workflow == "agile":
        if not task:
            print("Error: agile workflow requires a task. Use --task or --example to specify a task.")
            return
        await agile_development_workflow(task)
    
    elif args.workflow == "dev":
        if not task:
            print("Error: dev workflow requires a task. Use --task or --example to specify a task.")
            return
        await use_python_dev_agent_streaming(task)
    
    elif args.workflow == "review":
        if not args.code:
            print("Error: review workflow requires code. Use --code to provide code to review.")
            return
        result = await use_code_reviewer_agent(args.code)
        print("\nReview result:")
        print("-" * 50)
        print(result.chat_message.content)
    
    elif args.workflow == "dev_review":
        if not task:
            print("Error: dev_review workflow requires a task. Use --task or --example to specify a task.")
            return
        await develop_and_review(task)


if __name__ == "__main__":
    asyncio.run(main()) 