# IT Admin Agent System

An intelligent multi-agent system designed to automate, manage, and optimize IT administration tasks in datacenter environments.

## Overview

The IT Admin Agent System is a comprehensive solution that uses multiple specialized agents to handle routine IT administration tasks in datacenters. The system can autonomously execute tasks, learn from successful executions, and improve over time.

Key capabilities include:
- **Task Automation**: Execute multi-step IT administration tasks
- **Learning**: Build knowledge from past experiences to improve future executions
- **Tool Integration**: Execute commands and scripts locally or remotely
- **Human Collaboration**: Tiered human involvement model with approval workflows

## Architecture

The system follows a modular architecture with these core components:

### Agent Types

- **Task Manager Agent**: Coordinates task planning and delegation
- **Execution Agent**: Runs commands and scripts on target systems
- **Diagnostics Agent**: Analyzes issues and proposes solutions
- **Learning Agent**: Processes successful tasks to improve future operations
- **Validation Agent**: Validates configurations and changes

### Core Components

- **Agent Orchestrator**: Manages all agent activities
- **Knowledge Base**: Stores past experiences, scripts, and configurations
- **Task Planner**: Plans multi-step tasks using LLMs
- **API Server**: Provides REST API for external system integration
- **Dashboard**: Web-based UI for monitoring and control
- **CLI Interface**: Command-line interface for scripting and automation

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to systems being managed
- OpenAI API key (for LLM-based planning and learning)

### Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd itadmin_agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key:
   ```
   export OPENAI_API_KEY=your_api_key
   ```

4. Run the setup script to initialize the environment:
   ```
   ./setup.py
   ```
   
   This script will:
   - Check your environment for dependencies
   - Create necessary directories
   - Initialize the database structure
   - Create an example migration file

   Options:
   - `--force`: Force setup even if environment checks fail
   - `--skip-checks`: Skip environment dependency checks
   - `--log-level`: Set logging level

### Docker Installation

For containerized deployment:

1. Build and start using docker-compose:
   ```
   ./docker.sh up
   ```

2. Or for development mode:
   ```
   ./docker.sh --env dev up
   ```

For more Docker options:
```
./docker.sh --help
```

## Usage

### Starting the System

Run the system in full mode (agents, API, and dashboard):
```
python main.py --mode full
```

Or run specific components:
```
python main.py --mode api        # API server only
python main.py --mode dashboard  # Dashboard only
python main.py --mode agent-only # Agents only
```

### Accessing the Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

### Using the CLI

The command-line interface provides easy access to all system functionality:

```bash
# List all tasks
./cli.py list

# Get details of a specific task
./cli.py get <task_id>

# Create a new task
./cli.py create server_configure "Configure Nginx on web server" -p hostname=web01.example.com -p config_type=nginx

# Approve a task
./cli.py approve <task_id>

# Cancel a task
./cli.py cancel <task_id>
```

For detailed CLI help:
```
./cli.py --help
```

### API Usage

The system provides a REST API for integration with other systems:

- `GET /tasks`: List all tasks
- `GET /tasks/{task_id}`: Get details of a specific task
- `POST /tasks`: Create a new task
- `POST /tasks/{task_id}/approve`: Approve a task
- `POST /tasks/{task_id}/cancel`: Cancel a task

Example for creating a task:
```json
{
  "type": "server_configure",
  "description": "Configure Nginx on web server",
  "parameters": {
    "hostname": "web01.example.com",
    "config_type": "nginx",
    "config_template": "load_balancer"
  },
  "priority": "medium"
}
```

## Demo Scenarios

The system includes several demonstration scenarios to showcase its capabilities:

### Server Configuration

- [Nginx Web Server Setup](demos/server_config/nginx_setup.yaml): Deploy and configure a web server with Nginx
- Database Server Setup: Configure PostgreSQL with optimized settings
- Load Balancer Configuration: Set up HAProxy for load balancing

### Diagnostics

- [Network Diagnostics](demos/diagnostics/network_diagnosis.yaml): Comprehensive network troubleshooting
- Performance Analysis: Identify and resolve system bottlenecks
- Log Analysis: Extract insights from system logs

### Maintenance

- [Security Updates](demos/maintenance/security_updates.yaml): Apply security patches with validation
- Backup and Restore: Scheduled backups and test restores
- Disk Space Management: Clean up and optimize disk usage

For detailed information on demo scenarios, see the [demos directory](demos/index.md).

## Development

### Project Structure

```
itadmin_agent/
├── agent/              # Agent implementations
├── api/                # API server
├── config/             # Configuration
├── knowledge_base/     # Knowledge storage
├── task_planner/       # Task planning
├── ui/                 # Dashboard UI
├── utils/              # Utility modules
├── tests/              # Test suite
├── demos/              # Demo scenarios
├── docker/             # Docker configuration
├── main.py             # Main entry point
└── requirements.txt    # Dependencies
```

### Running Tests

```bash
# Run all tests
./run_tests.py

# Run only unit tests
./run_tests.py --unit

# Generate coverage report
./run_tests.py --coverage
```

### Adding New Agents

1. Create a new agent module in the `agent/` directory
2. Implement the agent interface with `start()`, `stop()`, and `execute_step()` methods
3. Register the agent in the `AgentOrchestrator` class

## License

[MIT License](LICENSE)

## Acknowledgements

- OpenAI - For the LLM models powering task planning and learning
- LangChain - For LLM integration components
- FastAPI - For the REST API implementation
- Streamlit - For the dashboard UI 