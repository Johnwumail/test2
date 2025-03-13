# Ubuntu OS Installation on Dell PowerEdge Server - Guide

This guide walks you through installing Ubuntu Server 22.04 LTS on a Dell PowerEdge server using the IT Admin Agent's integration with iDRAC Redfish API. This automation eliminates the need for physical access to the server and provides a consistent, reproducible installation process.

## Prerequisites

1. **Dell PowerEdge Server** with iDRAC Enterprise license
2. **Network connectivity** to the iDRAC interface
3. **iDRAC credentials** with administrator privileges
4. **Ubuntu Server ISO** accessible via HTTP(S), NFS, or CIFS
5. **IT Admin Agent** system up and running

## Understanding the Process

This demo uses the Redfish API to:
1. Connect to the iDRAC interface
2. Configure RAID (if specified)
3. Mount the Ubuntu ISO as a virtual media
4. Configure boot order
5. Launch a remote installation
6. Monitor installation progress
7. Perform post-installation validation

## Step-by-Step Instructions

### 1. Prepare the Configuration

Open the `ubuntu_poweredge_install.yaml` file and update the following key sections:

#### iDRAC Connection Information
```yaml
idrac:
  hostname: "idrac-server01.example.com"  # Update with your iDRAC IP/hostname
  username: "root"                        # Update with your iDRAC username
  password: "{{ idrac_password }}"        # Use environment variable or provide directly
```

#### Server and OS Information
```yaml
server:
  model: "PowerEdge R740"                 # Update with your server model
  service_tag: "ABC1234"                  # Update with your service tag (optional)

os:
  version: "22.04 LTS"                    # Update if using a different version
```

#### Storage Configuration
```yaml
storage:
  raid_level: "1"                         # Change based on your requirements
  disks_to_use: "all"                     # Specify specific disks if needed
```

#### Network Configuration
```yaml
network:
  dhcp: false                             # Set to true to use DHCP
  static:
    ip_address: "192.168.1.100"           # Update with your desired IP
    subnet_mask: "255.255.255.0"
    gateway: "192.168.1.1"
    dns_servers:
      - "192.168.1.10"
      - "8.8.8.8"
  hostname: "ubuntu-server01"             # Update with your desired hostname
```

#### ISO Location
```yaml
redfish:
  iso:
    source_type: "http"
    source_path: "http://mirrors.example.com/ubuntu-22.04-server-amd64.iso"  # Update with actual ISO location
```

### 2. Set Required Environment Variables

The demo uses environment variables for sensitive information. Set these before running:

```bash
export ITADMIN_IDRAC_PASSWORD="your-idrac-password"
export ITADMIN_ADMIN_PASSWORD="desired-ubuntu-admin-password"
export ITADMIN_ADMIN_SSH_KEY="ssh-rsa AAAA..."
```

### 3. Run the Installation Task

#### Using the CLI

```bash
# Navigate to the IT Admin Agent directory
cd itadmin_agent

# Run the task
./cli.py create server_provision "Install Ubuntu on PowerEdge Server" --parameters-file demos/server_provisioning/ubuntu_poweredge_install.yaml
```

#### Using the Dashboard

1. Open your browser and navigate to the IT Admin Agent dashboard (http://localhost:8501)
2. Click on "Create Task"
3. Set the following:
   - Task Type: `server_provision`
   - Description: "Install Ubuntu on PowerEdge Server"
   - Parameters: Copy and paste the content of `ubuntu_poweredge_install.yaml` with your modifications
   - Priority: High
4. Click "Create Task"

### 4. Monitor the Installation

The installation process typically takes 30-60 minutes depending on server specifications and network speed.

#### Using the CLI

```bash
# Check task status (replace TASK_ID with your actual task ID)
./cli.py get TASK_ID --follow
```

#### Using the Dashboard

1. Navigate to "Tasks" in the dashboard
2. Find your task in the list and click on it to view details
3. You'll see the various steps as they execute, including:
   - iDRAC connection
   - Hardware inventory
   - Storage configuration
   - ISO mounting
   - Boot configuration
   - Installation progress
   - Post-installation validation

### 5. Installation Steps Breakdown

During execution, the IT Admin Agent will:

1. **Connect to iDRAC** using the Redfish API
2. **Perform pre-checks** to ensure the server is ready for installation
3. **Configure storage** based on the RAID level specified
4. **Upload and mount the ISO** as virtual media
5. **Configure one-time boot** to the virtual media
6. **Power cycle the server** to begin installation
7. **Monitor the installation progress** via Redfish
8. **Wait for installation completion** 
9. **Perform post-installation validation** to ensure the server is properly configured
10. **Send notifications** about the completion status

### 6. Verification

After the task completes successfully:

1. Verify the server is accessible via SSH:
   ```bash
   ssh admin@192.168.1.100
   ```

2. Check that all specified packages are installed:
   ```bash
   dpkg -l | grep -E 'openssh-server|vim|htop|net-tools|curl|python3'
   ```

3. Verify network configuration:
   ```bash
   ip addr
   cat /etc/netplan/*.yaml
   ```

4. Check system logs for any errors:
   ```bash
   sudo journalctl -b | grep -i error
   ```

## Troubleshooting

If the installation fails, check the following:

1. **iDRAC Connectivity**: Ensure you can access the iDRAC interface via web browser
2. **ISO Accessibility**: Verify the ISO URL is accessible from the IT Admin Agent system
3. **Storage Configuration**: Check if there are existing RAID configurations that need to be cleared
4. **Installation Logs**: Review the task logs in the IT Admin Agent dashboard

Common error scenarios and solutions:

| Error | Solution |
|-------|----------|
| iDRAC connection timeout | Check network connectivity and verify iDRAC credentials |
| Virtual media mount failure | Ensure ISO URL is accessible and correctly formatted |
| RAID configuration failure | Check disk health and existing configurations |
| Installation timeout | Increase the timeout values in the configuration file |

## Advanced Customization

The demo configuration supports several advanced customizations:

1. **Preseed Files**: Add custom Ubuntu preseed configurations:
   ```yaml
   redfish:
     iso:
       preseed_file: "templates/custom_preseed.cfg"
   ```

2. **Custom Partitioning**: Define specific partition schemes:
   ```yaml
   storage:
     partitions:
       - mount: "/"
         size: "50G"
         filesystem: "ext4"
       - mount: "/var"
         size: "20G"
         filesystem: "ext4"
       - mount: "/home"
         size: "remaining"
         filesystem: "ext4"
   ```

3. **Post-Installation Scripts**: Execute custom scripts after installation:
   ```yaml
   post_install:
     scripts:
       - "scripts/setup_monitoring.sh"
       - "scripts/configure_backups.sh"
   ```

## Security Considerations

1. **iDRAC Credentials**: Always use environment variables or a secure credential store
2. **Network Security**: Ensure iDRAC interfaces are on a secure management network
3. **SSH Keys**: Prefer SSH key authentication over passwords
4. **Firmware Updates**: Consider running firmware updates before OS installation

## Expected Results

After successful completion, you will have:

1. A Dell PowerEdge server with Ubuntu 22.04 LTS installed
2. Properly configured RAID and storage
3. Network settings applied as specified
4. Initial user account created with SSH access
5. Basic security measures implemented (firewall, SSH hardening)
6. Specified packages installed and configured
7. A detailed report of the installation process and validation results 