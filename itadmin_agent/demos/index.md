# IT Admin Agent Demo Scenarios Index

This is a comprehensive list of all available demo scenarios for the IT Admin Agent system. Each demo includes configuration files and step-by-step guides to showcase the agent's capabilities in real-world IT administration tasks.

## Server Configuration Demos

| Demo | Description | Configuration | Guide |
|------|-------------|---------------|-------|
| Nginx Web Server Setup | Deploy and configure a web server with Nginx | [nginx_setup.yaml](server_config/nginx_setup.yaml) | [Guide](server_config/nginx_setup_guide.md) |
| Database Server | Set up a PostgreSQL database server | [postgresql_setup.yaml](server_config/postgresql_setup.yaml) | Coming soon |
| Load Balancer Configuration | Configure HAProxy as a load balancer | [haproxy_setup.yaml](server_config/haproxy_setup.yaml) | Coming soon |

## Diagnostics Demos

| Demo | Description | Configuration | Guide |
|------|-------------|---------------|-------|
| Network Diagnostics | Diagnose network connectivity issues | [network_diagnosis.yaml](diagnostics/network_diagnosis.yaml) | Coming soon |
| Performance Analysis | Identify and resolve performance bottlenecks | [performance_analysis.yaml](diagnostics/performance_analysis.yaml) | Coming soon |
| Log Analysis | Extract insights from system logs | [log_analysis.yaml](diagnostics/log_analysis.yaml) | Coming soon |

## Maintenance Demos

| Demo | Description | Configuration | Guide |
|------|-------------|---------------|-------|
| Security Updates | Apply security patches and updates | [security_updates.yaml](maintenance/security_updates.yaml) | Coming soon |
| Backup and Restore | Perform scheduled backups and test restores | [backup_restore.yaml](maintenance/backup_restore.yaml) | Coming soon |
| Disk Space Management | Identify and clean up disk space usage | [disk_cleanup.yaml](maintenance/disk_cleanup.yaml) | Coming soon |

## Using These Demos

Each demo configuration file (YAML) can be used with the IT Admin Agent in one of the following ways:

### Using the CLI

```bash
# Run a server configuration demo
./cli.py create server_configure "Set up Nginx web server" --parameters-file demos/server_config/nginx_setup.yaml

# Run a diagnostics demo
./cli.py create system_diagnose "Diagnose network connectivity issues" --parameters-file demos/diagnostics/network_diagnosis.yaml

# Run a maintenance demo
./cli.py create system_maintenance "Apply security updates" --parameters-file demos/maintenance/security_updates.yaml
```

### Using the Dashboard

1. Open the dashboard in your browser (http://localhost:8501)
2. Navigate to "Create Task"
3. Select the appropriate task type
4. Enter a description
5. Copy and paste the parameters from the demo YAML file
6. Submit the task

## Customizing Demos for Your Environment

Before running any demo, make sure to:

1. Update server hostnames, IP addresses, and credentials to match your environment
2. Review and modify any environment-specific settings
3. Consider running in a test environment first before targeting production systems

## Contributing New Demos

If you develop a useful demo scenario, consider contributing it to the project:

1. Create the configuration YAML file
2. Write a step-by-step guide (markdown)
3. Add it to this index
4. Submit a pull request to the repository 