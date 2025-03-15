"""
Model client implementations for AutoGen.
"""

import os
from typing import Optional, Dict, Any, List
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import UserMessage


def create_model_client(
    model_name: str = "gemini-2.0-flash",  # Use the default model from original model.py
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_info: Optional[Dict[str, Any]] = None
) -> OpenAIChatCompletionClient:
    """
    Create a model client for AutoGen.
    
    Args:
        model_name: Name of the model to use
        api_key: API key for the model provider
        base_url: Base URL for the model provider's API
        model_info: Model capabilities information
        
    Returns:
        An OpenAIChatCompletionClient instance
    """
    # Set default values based on model_name
    if model_name.startswith("gemini"):
        if not api_key:
            # Use environment variable or fallback to a placeholder
            api_key = os.environ.get('GEMINI_API_KEY', 'your_api_key_here')
            # Debug: Print the first few characters of the API key to verify it's not the placeholder
            if api_key == 'your_api_key_here':
                print("WARNING: Using placeholder API key. Please set GEMINI_API_KEY environment variable.")
            else:
                print(f"Using Gemini API key: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}")
        if not base_url:
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        if not model_info:
            model_info = {
                "json_output": True,
                "function_calling": True,
                "vision": True,
                "family": "gemini"
            }
    elif model_name.startswith("deepseek"):
        if not api_key:
            # Use environment variable for DeepSeek API key
            api_key = os.environ.get('DEEPSEEK_API_KEY', 'your_api_key_here')
            if api_key == 'your_api_key_here':
                print("WARNING: Using placeholder API key. Please set DEEPSEEK_API_KEY environment variable.")
        if not base_url:
            base_url = "https://api.deepseek.com/v1/"
        if not model_info:
            model_info = {
                "json_output": True,
                "function_calling": True,
                "vision": False,
                "family": "deepseek"
            }
            
    # Create and return the client
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        model_info=model_info
    )


# Default instance created from the original model.py
gemini_model_client = create_model_client(
    model_name="gemini-2.0-flash",
    api_key=os.environ.get('GEMINI_API_KEY', 'your_api_key_here'),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


async def test_model_client(
    client: Optional[OpenAIChatCompletionClient] = None, 
    query: str = "What is the capital of France?"
) -> Any:
    """
    Test a model client with a simple query.
    
    Args:
        client: The model client to test, defaults to gemini_model_client
        query: The test query to send to the model
        
    Returns:
        The model's response
    """
    if client is None:
        client = gemini_model_client
        
    result = await client.create([UserMessage(content=query, source="user")])
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_model_client()) 