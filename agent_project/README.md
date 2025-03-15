# AutoGen Scrum Team Project

This is a Python project built using the AutoGen framework, implementing a complete Scrum development team. The team consists of multiple specialized agents that collaborate to complete software development tasks.

## Project Structure

```
agent_project/
├── agent_project/
│   ├── __init__.py          # Package initialization with convenient imports
│   ├── agents/              # Agent definitions
│   │   ├── __init__.py
│   │   └── dev_agents.py    # Development team agents
│   ├── models/              # Model clients
│   │   ├── __init__.py
│   │   └── clients.py       # Various LLM model clients
│   └── teams/               # Team organization
│       ├── __init__.py
│       └── scrum_team.py    # Scrum team implementation
├── examples/                # Example code
│   └── test_model.py        # Test model client
├── main.py                  # Command-line entry point
├── setup.py                 # Installation script
├── requirements.txt         # Dependencies list
├── setup_env.py             # API key configuration helper
├── CONFIG.md                # Configuration guide
└── README.md                # Documentation
```

## Team Members

The project implements a Scrum team consisting of five specialized agents:

1. **Python Developer** - Responsible for writing high-quality Python code
2. **Code Reviewer** - Responsible for reviewing code and providing improvement suggestions
3. **Product Owner** - Defines requirements and feature priorities
4. **QA Engineer** - Tests code and identifies potential issues
5. **Scrum Master** - AI agent that facilitates the development process and provides guidance

## Installation

### Method 1: Install using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/agent-project.git
cd agent-project

# Install package (development mode)
pip install -e .
```

### Method 2: Direct use

```bash
# Clone the repository
git clone https://github.com/yourusername/agent-project.git
cd agent-project

# Install dependencies
pip install -r requirements.txt
```

## API Key Configuration

This project requires API keys to access language models. For security reasons, these keys should be stored as environment variables, not in your code.

### Quick Setup

Run the included setup script to configure your API keys:

```bash
# From the project root directory
python setup_env.py
```

### Manual Setup

Set your API keys as environment variables:

```bash
# Linux/Mac
export GEMINI_API_KEY="your_api_key_here"

# Windows
set GEMINI_API_KEY=your_api_key_here
```

Alternatively, create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
DEEPSEEK_API_KEY=your_api_key_here
```

Then install python-dotenv:

```bash
pip install python-dotenv
```

> 📝 **Note:** See `CONFIG.md` for a complete configuration guide.
> 
> ⚠️ **Important:** Never commit API keys to version control!

## Usage

### Command-line Usage

The project provides a convenient command-line entry point supporting multiple workflows:

```bash
# Use Scrum team (default)
python main.py

# Specify a task
python main.py --task "Write a function to calculate Fibonacci sequence"

# Use example task
python main.py --example 1

# Use Agile development workflow
python main.py --workflow agile --task "Create a web crawler"

# Use only developer agent
python main.py --workflow dev --task "Implement quicksort algorithm"

# Code review
python main.py --workflow review --code "def add(a, b): return a + b"

# Development and review workflow
python main.py --workflow dev_review --task "Write a binary search algorithm"
```

### Library Usage

You can also import and use it in your own Python code:

```python
import asyncio
from agent_project import use_scrum_team, agile_development_workflow

# Use Scrum team
asyncio.run(use_scrum_team("Create a calculator application"))

# Or use Agile development workflow
asyncio.run(agile_development_workflow("Write a function to validate URLs"))
```

### Customizing Models

You can customize which model to use:

```python
from agent_project.models import create_model_client

# Create custom model client
custom_client = create_model_client(
    model_name="gemini-1.5-flash",
    api_key="your_api_key",  # Optional
    model_info={
        "json_output": True,
        "function_calling": True,
        "vision": False,
        "family": "gemini"
    }
)
```

## Workflow Types

### 1. Scrum Team Workflow

Uses `SelectorGroupChat` to implement dynamic team collaboration, where team members intelligently select the next speaker based on context:

```python
from agent_project import use_scrum_team
import asyncio

asyncio.run(use_scrum_team("Create a secure password hashing tool with salt functionality"))
```

### 2. Agile Development Workflow

Uses `RoundRobinGroupChat` to implement team collaboration with a fixed order:

```python
from agent_project import agile_development_workflow
import asyncio

asyncio.run(agile_development_workflow("Write a function to check for prime numbers"))
```

### 3. Development and Review Workflow

Executes development and review process in steps:

```python
from agent_project import develop_and_review
import asyncio

asyncio.run(develop_and_review("Implement Fibonacci sequence calculation using recursion"))
```

### 4. Single Agent Usage

```python
from agent_project import use_python_dev_agent_streaming, use_code_reviewer_agent
import asyncio

# Use developer agent
asyncio.run(use_python_dev_agent_streaming("Create a class representing playing cards"))

# Use code reviewer agent
code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
"""
result = asyncio.run(use_code_reviewer_agent(code))
print(result.chat_message.content)
```

## Local Code Execution

All agents can use `LocalCommandLineCodeExecutor` to execute code in a secure local environment:

```python
from agent_project.agents.dev_agents import execute_code
import asyncio

code = """
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 10, 100)
y = np.sin(x)
plt.plot(x, y)
plt.title("Sine Wave")
plt.savefig("sine.png")
print("Plot saved as sine.png")
"""

asyncio.run(execute_code(code))
```

## Dependencies

- autogen-core>=0.4.0
- autogen-ext[openai]>=0.4.0
- autogen-agentchat>=0.4.0
- autogen-ext[local-code-execution]>=0.4.0

## License

MIT 