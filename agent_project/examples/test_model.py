#!/usr/bin/env python
"""
Example script to test the model client.
"""

import asyncio
from agent_project.models import create_model_client, test_model_client

async def main():
    """Test the model client with a simple query."""
    # Create a model client (using default Gemini settings)
    client = create_model_client()
    
    # Test with different queries
    queries = [
        "What is the capital of France?",
        "Explain quantum computing in simple terms.",
        "Write a short poem about AI."
    ]
    
    for query in queries:
        print(f"\n\nQuery: {query}")
        print("-" * 50)
        result = await test_model_client(client, query)
        print(f"Response: {result.chat_message.content}")
    
    # Example of creating a custom model client
    custom_client = create_model_client(
        model_name="gemini-1.5-flash",  # Use a different model
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": False,
            "family": "gemini"
        }
    )
    
    print("\n\nCustom Client Test")
    print("-" * 50)
    result = await test_model_client(custom_client, "What's the weather like today?")
    print(f"Response: {result.chat_message.content}")


if __name__ == "__main__":
    asyncio.run(main()) 