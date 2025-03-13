# Nginx Web Server Setup Demo Guide

This guide walks you through setting up a web server using Nginx via the IT Admin Agent system. This demo showcases the agent's server configuration capabilities.

## Prerequisites

- A target server (VM or physical) running a supported Linux distribution (Ubuntu, Debian, CentOS, etc.)
- SSH access to the target server
- IT Admin Agent system up and running

## Demo Steps

### 1. Prepare the Target Server

Ensure your target server meets these requirements:
- SSH access is configured
- The user has sudo privileges
- The server has internet access for package installation

### 2. Customize the Configuration

Open the `nginx_setup.yaml` file and modify the following:

```yaml
# Target server information
hostname: "web01.example.com"  # Replace with your actual server hostname
username: "admin"              # SSH username for connection
port: 22                       # SSH port (default: 22)
```

You can also customize other settings like:
- Nginx configuration (worker processes, connections, etc.)
- Security settings (firewall rules, SSL settings)
- Demo site content

### 3. Run the Configuration Task

#### Using the CLI

```bash
# Navigate to the IT Admin Agent directory
cd itadmin_agent

# Run the task
./cli.py create server_configure "Set up Nginx web server" --parameters-file demos/server_config/nginx_setup.yaml
```

#### Using the Dashboard

1. Open your browser and navigate to the IT Admin Agent dashboard (http://localhost:8501)
2. Click on "Create Task"
3. Set the following:
   - Task Type: `server_configure`
   - Description: "Set up Nginx web server"
   - Parameters: Copy and paste the content of `nginx_setup.yaml`
   - Priority: Medium
4. Click "Create Task"

### 4. Monitor the Task Execution

#### Using the CLI

```bash
# Check task status (replace TASK_ID with your actual task ID)
./cli.py get TASK_ID
```

#### Using the Dashboard

1. Navigate to "Tasks" in the dashboard
2. Find your task in the list and click on it to view details
3. You'll see the various steps as they execute

### 5. Verification

After the task completes successfully:

1. Open a web browser and navigate to your server's IP address or hostname
2. You should see the demo web page with "Welcome to Nginx" and other configured content
3. Check that HTTPS works if you enabled SSL
4. Verify that the server is properly hardened by checking:
   - Firewall rules: `sudo ufw status` or `sudo iptables -L`
   - Nginx configuration: `sudo nginx -T`
   - Security headers: Use a tool like [Security Headers](https://securityheaders.com) to check your site

## Troubleshooting

If the task fails or encounters issues:

1. Check the task details in the dashboard or CLI for error messages
2. Verify SSH connectivity to the target server
3. Check server logs:
   - Nginx logs: `/var/log/nginx/error.log`
   - System logs: `/var/log/syslog` or `/var/log/messages`
4. Ensure the server has sufficient disk space and resources

## Expected Results

After successful completion, you will have:

1. A fully configured Nginx web server with optimized settings
2. Proper security hardening (firewall, TLS, security headers)
3. A demo website to verify functionality
4. Detailed logs and reports from the agent about the configuration process

This demo showcases how the IT Admin Agent can automate complex server setup and configuration tasks that would otherwise require manual effort and specialized knowledge. 