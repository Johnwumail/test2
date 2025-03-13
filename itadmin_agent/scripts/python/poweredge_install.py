#!/usr/bin/env python3
"""
PowerEdge Server OS Installation Script

This script uses the Redfish API to automate the installation of operating systems 
on Dell PowerEdge servers via iDRAC.
"""
import sys
import time
import json
import argparse
import logging
import requests
import urllib3
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Suppress insecure HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("poweredge_install")


class RedfishClient:
    """Client for interacting with iDRAC Redfish API."""
    
    def __init__(self, hostname: str, username: str, password: str, port: int = 443, verify_ssl: bool = False):
        """
        Initialize Redfish client.
        
        Args:
            hostname: iDRAC hostname or IP address
            username: iDRAC username
            password: iDRAC password
            port: iDRAC port (default: 443)
            verify_ssl: Whether to verify SSL certificates (default: False)
        """
        self.base_url = f"https://{hostname}:{port}/redfish/v1"
        self.auth = (username, password)
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = self.verify_ssl
        
        # Test connection
        try:
            response = self.session.get(f"{self.base_url}/Systems")
            response.raise_for_status()
            logger.info(f"Successfully connected to Redfish API at {hostname}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Redfish API: {e}")
            raise
    
    def get_systems(self) -> List[Dict[str, Any]]:
        """
        Get all systems managed by iDRAC.
        
        Returns:
            List of system information dictionaries
        """
        response = self.session.get(f"{self.base_url}/Systems")
        response.raise_for_status()
        data = response.json()
        
        systems = []
        for member in data.get('Members', []):
            system_url = member.get('@odata.id')
            if system_url:
                system_data = self.session.get(f"https://{self.base_url.split('/')[2]}{system_url}").json()
                systems.append(system_data)
        
        return systems
    
    def get_system_id(self) -> str:
        """
        Get the ID of the first system managed by iDRAC.
        
        Returns:
            System ID
        """
        response = self.session.get(f"{self.base_url}/Systems")
        response.raise_for_status()
        data = response.json()
        
        if data.get('Members') and len(data.get('Members')) > 0:
            system_url = data.get('Members')[0].get('@odata.id')
            return system_url.split('/')[-1]
        
        raise ValueError("No systems found")
    
    def get_storage_controllers(self, system_id: str) -> List[Dict[str, Any]]:
        """
        Get all storage controllers for a system.
        
        Args:
            system_id: System ID
            
        Returns:
            List of storage controller information dictionaries
        """
        response = self.session.get(f"{self.base_url}/Systems/{system_id}/Storage")
        response.raise_for_status()
        data = response.json()
        
        controllers = []
        for member in data.get('Members', []):
            controller_url = member.get('@odata.id')
            if controller_url:
                controller_data = self.session.get(f"https://{self.base_url.split('/')[2]}{controller_url}").json()
                controllers.append(controller_data)
        
        return controllers
    
    def get_physical_disks(self, system_id: str, controller_id: str) -> List[Dict[str, Any]]:
        """
        Get all physical disks for a storage controller.
        
        Args:
            system_id: System ID
            controller_id: Storage controller ID
            
        Returns:
            List of physical disk information dictionaries
        """
        response = self.session.get(f"{self.base_url}/Systems/{system_id}/Storage/{controller_id}/Drives")
        response.raise_for_status()
        data = response.json()
        
        disks = []
        for member in data.get('Members', []):
            disk_url = member.get('@odata.id')
            if disk_url:
                disk_data = self.session.get(f"https://{self.base_url.split('/')[2]}{disk_url}").json()
                disks.append(disk_data)
        
        return disks
    
    def create_raid_volume(self, system_id: str, controller_id: str, 
                           raid_type: str, disk_ids: List[str], 
                           volume_name: str = "OS_Volume") -> str:
        """
        Create a RAID volume.
        
        Args:
            system_id: System ID
            controller_id: Storage controller ID
            raid_type: RAID type (0, 1, 5, 6, 10)
            disk_ids: List of physical disk IDs
            volume_name: Name of the volume
            
        Returns:
            Job ID for the RAID creation task
        """
        # Map raid_type to Redfish values
        raid_map = {
            "0": "RAID0",
            "1": "RAID1",
            "5": "RAID5",
            "6": "RAID6",
            "10": "RAID10"
        }
        
        raid_level = raid_map.get(raid_type, "RAID1")
        
        # Format disk IDs for Redfish
        drives = [{"@odata.id": f"{self.base_url}/Systems/{system_id}/Storage/{controller_id}/Drives/{disk_id}"} 
                 for disk_id in disk_ids]
        
        payload = {
            "VolumeType": "Mirrored",
            "RAIDType": raid_level,
            "Name": volume_name,
            "Drives": drives
        }
        
        response = self.session.post(
            f"{self.base_url}/Systems/{system_id}/Storage/{controller_id}/Volumes",
            json=payload
        )
        response.raise_for_status()
        
        # Get the job ID from the response
        if response.status_code == 202:  # Accepted
            job_id = response.headers.get('Location', '').split('/')[-1]
            logger.info(f"RAID volume creation job started with ID: {job_id}")
            return job_id
        
        raise ValueError(f"Failed to create RAID volume: {response.text}")
    
    def mount_virtual_media(self, system_id: str, iso_url: str, media_type: str = "CD") -> bool:
        """
        Mount an ISO as virtual media.
        
        Args:
            system_id: System ID
            iso_url: URL to the ISO file
            media_type: Media type (CD, DVD, USB)
            
        Returns:
            True if successful
        """
        # Get the virtual media collection
        response = self.session.get(f"{self.base_url}/Systems/{system_id}/VirtualMedia")
        response.raise_for_status()
        data = response.json()
        
        # Find the appropriate virtual media endpoint
        media_url = None
        for member in data.get('Members', []):
            member_url = member.get('@odata.id')
            if member_url:
                member_data = self.session.get(f"https://{self.base_url.split('/')[2]}{member_url}").json()
                if member_data.get('MediaTypes') and media_type in member_data.get('MediaTypes'):
                    media_url = member_url
                    break
        
        if not media_url:
            raise ValueError(f"No virtual media endpoint found for type {media_type}")
        
        # Insert the virtual media
        payload = {
            "Image": iso_url,
            "Inserted": True,
            "WriteProtected": True
        }
        
        response = self.session.post(
            f"https://{self.base_url.split('/')[2]}{media_url}/Actions/VirtualMedia.InsertMedia",
            json=payload
        )
        response.raise_for_status()
        
        logger.info(f"ISO image {iso_url} mounted successfully")
        return True
    
    def set_one_time_boot(self, system_id: str, boot_source: str = "Cd") -> bool:
        """
        Set one-time boot source.
        
        Args:
            system_id: System ID
            boot_source: Boot source (Pxe, Cd, Hdd, Usb, Utilities, UefiTarget)
            
        Returns:
            True if successful
        """
        payload = {
            "Boot": {
                "BootSourceOverrideEnabled": "Once",
                "BootSourceOverrideTarget": boot_source
            }
        }
        
        response = self.session.patch(
            f"{self.base_url}/Systems/{system_id}",
            json=payload
        )
        response.raise_for_status()
        
        logger.info(f"One-time boot set to {boot_source}")
        return True
    
    def power_cycle_server(self, system_id: str) -> bool:
        """
        Power cycle the server.
        
        Args:
            system_id: System ID
            
        Returns:
            True if successful
        """
        # Check current power state
        response = self.session.get(f"{self.base_url}/Systems/{system_id}")
        response.raise_for_status()
        data = response.json()
        
        current_state = data.get('PowerState')
        
        # Determine action based on current state
        if current_state == "Off":
            action = "On"
        else:
            action = "GracefulRestart"
        
        payload = {
            "ResetType": action
        }
        
        response = self.session.post(
            f"{self.base_url}/Systems/{system_id}/Actions/ComputerSystem.Reset",
            json=payload
        )
        response.raise_for_status()
        
        logger.info(f"Server power action {action} initiated")
        return True
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status information
        """
        response = self.session.get(f"{self.base_url}/TaskService/Tasks/{job_id}")
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_job_completion(self, job_id: str, check_interval: int = 30, timeout: int = 3600) -> Dict[str, Any]:
        """
        Wait for a job to complete.
        
        Args:
            job_id: Job ID
            check_interval: Interval between status checks in seconds
            timeout: Maximum time to wait in seconds
            
        Returns:
            Final job status information
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            job_status = self.check_job_status(job_id)
            state = job_status.get('TaskState')
            
            logger.info(f"Job {job_id} is in state: {state}")
            
            if state == "Completed":
                logger.info(f"Job {job_id} completed successfully")
                return job_status
            elif state in ["Failed", "Cancelled", "Exception"]:
                message = job_status.get('Messages', [{}])[0].get('Message', 'No error message')
                logger.error(f"Job {job_id} failed: {message}")
                raise ValueError(f"Job failed: {message}")
            
            # Wait before checking again
            time.sleep(check_interval)
        
        logger.error(f"Timeout waiting for job {job_id} to complete")
        raise TimeoutError(f"Timeout waiting for job {job_id} to complete")
    
    def get_server_health(self, system_id: str) -> Dict[str, Any]:
        """
        Get server health information.
        
        Args:
            system_id: System ID
            
        Returns:
            Server health information
        """
        response = self.session.get(f"{self.base_url}/Systems/{system_id}")
        response.raise_for_status()
        data = response.json()
        
        health = {
            "status": data.get('Status', {}).get('Health'),
            "state": data.get('Status', {}).get('State'),
            "power_state": data.get('PowerState'),
            "model": data.get('Model'),
            "manufacturer": data.get('Manufacturer'),
            "serial_number": data.get('SerialNumber'),
            "bios_version": data.get('BiosVersion')
        }
        
        return health


def parse_config(config_file: str) -> Dict[str, Any]:
    """
    Parse configuration file.
    
    Args:
        config_file: Path to configuration YAML file
        
    Returns:
        Configuration dictionary
    """
    with open(config_file, 'r') as f:
        try:
            config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise


def install_os(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Install OS on PowerEdge server using Redfish.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Result of installation
    """
    # Initialize the Redfish client
    client = RedfishClient(
        hostname=config['idrac']['hostname'],
        username=config['idrac']['username'],
        password=config['idrac']['password'],
        port=config['idrac'].get('port', 443),
        verify_ssl=config['idrac'].get('verify_ssl', False)
    )
    
    # Get the system ID
    system_id = client.get_system_id()
    logger.info(f"Using system ID: {system_id}")
    
    # Check server health
    health = client.get_server_health(system_id)
    logger.info(f"Server health: {health}")
    
    if health['status'] != 'OK' and health['status'] != 'Warning':
        logger.error(f"Server health is not OK: {health['status']}")
        if not config.get('force', False):
            raise ValueError(f"Server health is not OK: {health['status']}")
    
    # Configure RAID if requested
    if config.get('storage', {}).get('raid_level'):
        raid_level = config['storage']['raid_level']
        logger.info(f"Configuring RAID {raid_level}")
        
        # Get storage controllers
        controllers = client.get_storage_controllers(system_id)
        if not controllers:
            raise ValueError("No storage controllers found")
        
        controller_id = controllers[0]['Id']
        logger.info(f"Using storage controller: {controller_id}")
        
        # Get physical disks
        disks = client.get_physical_disks(system_id, controller_id)
        if not disks:
            raise ValueError("No physical disks found")
        
        # Filter disks if specific ones are requested
        if config['storage'].get('disks_to_use') and config['storage']['disks_to_use'] != 'all':
            disk_ids = config['storage']['disks_to_use']
        else:
            disk_ids = [disk['Id'] for disk in disks]
        
        logger.info(f"Using disks: {disk_ids}")
        
        # Create RAID volume
        volume_name = f"OS_Volume_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_id = client.create_raid_volume(system_id, controller_id, raid_level, disk_ids, volume_name)
        
        # Wait for RAID configuration to complete
        client.wait_for_job_completion(
            job_id, 
            check_interval=config.get('redfish', {}).get('jobs', {}).get('check_interval', 30),
            timeout=config.get('redfish', {}).get('jobs', {}).get('timeout', 3600)
        )
    
    # Mount ISO
    iso_url = config['redfish']['iso']['source_path']
    logger.info(f"Mounting ISO: {iso_url}")
    client.mount_virtual_media(system_id, iso_url)
    
    # Set one-time boot to CD/DVD
    boot_target = config.get('redfish', {}).get('boot', {}).get('one_time_boot', 'Cd')
    logger.info(f"Setting one-time boot to: {boot_target}")
    client.set_one_time_boot(system_id, boot_target)
    
    # Power cycle the server to start installation
    logger.info("Power cycling server to start installation")
    client.power_cycle_server(system_id)
    
    # Wait for installation (this is an estimate, actual monitoring would require
    # additional methods like out-of-band console access or periodic polling)
    installation_timeout = config.get('redfish', {}).get('jobs', {}).get('timeout', 7200)
    logger.info(f"Installation started, will wait up to {installation_timeout} seconds")
    
    # In a real implementation, we would periodically check server status,
    # console logs, etc. to determine when installation is complete
    
    # For this demo, we'll just return success
    result = {
        "status": "success",
        "message": "OS installation initiated",
        "system_id": system_id,
        "timestamp": datetime.now().isoformat()
    }
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PowerEdge Server OS Installation")
    parser.add_argument("--config", required=True, help="Path to configuration YAML file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Log level")
    parser.add_argument("--force", action="store_true", help="Force installation even if server health is not OK")
    
    args = parser.parse_args()
    
    # Set log level
    logger.setLevel(getattr(logging, args.log_level))
    
    try:
        # Parse configuration
        config = parse_config(args.config)
        
        # Add force flag to config if specified
        if args.force:
            config['force'] = True
        
        # Install OS
        result = install_os(config)
        
        # Print result
        print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 