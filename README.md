# DeepSeek Model Client for AutoGen

This repository contains a simple AutoGen model client implementation for DeepSeek's API.

## Setup

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Alternatively, use the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. The model client is implemented in `model.py`, which loads configuration from `config.py`.

## Configuration

You can modify the model parameters in `config.py`:

```python
# DeepSeek API configuration
DEEPSEEK_CONFIG = {
    "model": "deepseek-chat",
    "api_key": "your_api_key",
    "base_url": "https://api.deepseek.com/v1",
    "model_parameters": {
        "temperature": 0.7,
        "max_tokens": 1000,
        # Add other parameters as needed
    },
    # Required for non-standard OpenAI models
    "model_info": {
        "json_output": True,  # Whether the model supports JSON output
        "function_calling": True,  # Whether the model supports function calling
        "vision": False,  # Whether the model supports vision/image inputs
        "family": "llama"  # The model family (e.g., llama, mistral, etc.)
    }
}
```

### Important Note on model_info
When using a non-standard OpenAI model (like DeepSeek), you must provide `model_info` to describe the model's capabilities. This tells AutoGen about the features supported by your model.

## Usage

You can run the test client with:
```bash
python model.py
```

To use this client in your own AutoGen applications, import it from `model.py`:
```python
from model import deepseek_model_client

# Use it with an AutoGen agent
from autogen_core.agents import Agent

agent = Agent(
    name="deepseek_agent",
    model_client=deepseek_model_client,
    system_message="You are a helpful assistant."
)

# Now use the agent in your application
``` 