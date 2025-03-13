# IT Admin Agent Demo Scenarios

This directory contains various demonstration scenarios for the IT Admin Agent system. These scenarios showcase common datacenter automation tasks and how they can be accomplished using the system.

## Available Demos

### Server Configuration

Demonstrations of server setup, configuration management, and application deployment:

- **Web Server Setup**: Deploy and configure a web server with Nginx
- **Database Server**: Set up a PostgreSQL database server
- **Load Balancer Configuration**: Configure HAProxy as a load balancer

### Diagnostics

Scenarios demonstrating troubleshooting and diagnostic capabilities:

- **Network Diagnostics**: Diagnose network connectivity issues
- **Performance Analysis**: Identify and resolve performance bottlenecks
- **Log Analysis**: Extract insights from system logs

### Maintenance

Routine maintenance tasks:

- **Security Updates**: Apply security patches and updates
- **Backup and Restore**: Perform scheduled backups and test restores
- **Disk Space Management**: Identify and clean up disk space usage

## Running the Demos

Each demo scenario includes:

1. A step-by-step guide
2. Sample parameters for the IT Admin Agent
3. Expected results and validation steps

### Using the CLI

```bash
# Run a server configuration demo
itadmin create server_configure "Set up Nginx web server" --parameters-file demos/server_config/nginx_setup.yaml

# Run a diagnostics demo
itadmin create system_diagnose "Diagnose network connectivity issues" --parameters-file demos/diagnostics/network_diagnosis.yaml

# Run a maintenance demo
itadmin create system_maintenance "Apply security updates" --parameters-file demos/maintenance/security_updates.yaml
```

### Using the Dashboard

1. Open the dashboard in your browser (http://localhost:8501)
2. Navigate to "Create Task"
3. Select the task type (e.g., "server_configure")
4. Enter a description
5. Copy and paste the parameters from the demo YAML file
6. Submit the task

## Creating Your Own Scenarios

You can use these demos as templates to create your own scenarios:

1. Create a YAML file with the parameters for your task
2. Document the steps and expected outcomes
3. Test with various server configurations

The demo scenarios are designed to be educational and serve as templates for real-world usage. 