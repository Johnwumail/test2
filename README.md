# IT Admin Agent System

An intelligent multi-agent system designed to automate, manage, and optimize IT administration tasks in datacenter environments.

## Project Overview

This repository contains the IT Admin Agent System, a comprehensive solution that uses multiple specialized agents to handle routine IT administration tasks in datacenters. For detailed information, please see the [IT Admin Agent README](itadmin_agent/README.md).

## Key Features

- **Task Automation**: Execute multi-step IT administration tasks
- **Learning**: Build knowledge from past experiences to improve future executions
- **Tool Integration**: Execute commands and scripts locally or remotely
- **Human Collaboration**: Tiered human involvement model with approval workflows
- **Diagnostics**: Intelligent system diagnostics capabilities
- **Maintenance**: Automate routine system maintenance

## Demo Scenarios

The system includes several demonstration scenarios to showcase its capabilities:

- Server Configuration
- Network Diagnostics
- System Maintenance
- Security Updates

For details on available demos, see the [Demo Index](itadmin_agent/demos/index.md).

## Getting Started

Please refer to the [IT Admin Agent Documentation](itadmin_agent/README.md) for installation and usage instructions.

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd itadmin-agent

# Install dependencies
pip install -r itadmin_agent/requirements.txt

# Run the system
cd itadmin_agent
python main.py --mode full
```

## License

[MIT License](LICENSE) 