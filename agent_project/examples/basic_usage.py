#!/usr/bin/env python
"""
Basic Usage Examples - Demonstrating core functionality of the refactored Agent Project
"""

import asyncio
import sys

# Import from the refactored package
from agent_project import (
    use_scrum_team,
    agile_development_workflow,
    use_python_dev_agent_streaming,
    use_code_reviewer_agent,
    develop_and_review
)


async def demo_scrum_team():
    """
    Demonstrate Scrum team workflow
    """
    print("\n\n===== Demonstrating Scrum Team Workflow =====\n")
    task = "Write a function to validate whether a given string is a valid IPv4 address"
    await use_scrum_team(task)


async def demo_agile_workflow():
    """
    Demonstrate agile development workflow
    """
    print("\n\n===== Demonstrating Agile Development Workflow =====\n")
    task = "Write a function to convert Roman numerals to integers"
    await agile_development_workflow(task)


async def demo_python_dev():
    """
    Demonstrate Python developer agent
    """
    print("\n\n===== Demonstrating Python Developer Agent =====\n")
    task = "Write a simple logging class supporting different log levels"
    await use_python_dev_agent_streaming(task)


async def demo_code_review():
    """
    Demonstrate code reviewer agent
    """
    print("\n\n===== Demonstrating Code Reviewer Agent =====\n")
    code = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""
    result = await use_code_reviewer_agent(code)
    print(f"Review result: {result.chat_message.content}")


async def demo_dev_and_review():
    """
    Demonstrate development and review workflow
    """
    print("\n\n===== Demonstrating Development and Review Workflow =====\n")
    task = "Write a function implementing the quicksort algorithm"
    await develop_and_review(task)


async def main():
    """
    Demonstrate all examples
    """
    if len(sys.argv) > 1:
        # If command line arguments are provided, run specific example
        example = sys.argv[1].lower()
        if example == "scrum":
            await demo_scrum_team()
        elif example == "agile":
            await demo_agile_workflow()
        elif example == "dev":
            await demo_python_dev()
        elif example == "review":
            await demo_code_review()
        elif example == "dev_review":
            await demo_dev_and_review()
        else:
            print(f"Unknown example: {example}")
            print("Available examples: scrum, agile, dev, review, dev_review")
    else:
        # If no command line arguments, run the simplest example
        print("Running Python developer example (usage: python basic_usage.py [scrum|agile|dev|review|dev_review])")
        await demo_python_dev()


if __name__ == "__main__":
    asyncio.run(main()) 