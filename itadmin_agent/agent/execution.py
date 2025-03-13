"""
Execution Agent

This module implements the Execution Agent which is responsible for executing commands
and scripts on target systems.
"""
import os
import json
import subprocess
import tempfile
import shutil
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

import paramiko
from paramiko.ssh_exception import SSHException

from utils.logging_setup import get_agent_logger


class ExecutionAgent:
    """
    Execution Agent for the IT Admin Agent system.
    
    This class is responsible for:
    - Executing commands on local and remote systems
    - Running scripts with proper isolation
    - Handling command execution failures
    - Collecting execution results
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Execution Agent.
        
        Args:
            config: Configuration dictionary for the execution agent
        """
        self.logger = get_agent_logger("execution")
        self.logger.info("Initializing Execution Agent")
        
        self.config = config
        self.is_running = False
        self.shutdown_flag = threading.Event()
        
        # Create a dictionary to store ssh clients
        self.ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self.ssh_clients_lock = threading.RLock()
        
        # Create sandbox directory if needed
        self.sandbox_dir = Path(tempfile.gettempdir()) / "itadmin_sandbox"
        if self.config.get('sandbox_enabled', True):
            os.makedirs(self.sandbox_dir, exist_ok=True)
            self.logger.info(f"Created sandbox directory: {self.sandbox_dir}")
        
        self.logger.info("Execution Agent initialized")
    
    def start(self) -> None:
        """Start the Execution Agent."""
        if self.is_running:
            self.logger.warning("Execution Agent is already running")
            return
        
        self.logger.info("Starting Execution Agent")
        self.shutdown_flag.clear()
        self.is_running = True
        self.logger.info("Execution Agent started")
    
    def stop(self) -> None:
        """Stop the Execution Agent."""
        if not self.is_running:
            self.logger.warning("Execution Agent is not running")
            return
        
        self.logger.info("Stopping Execution Agent")
        self.shutdown_flag.set()
        
        # Close all SSH connections
        with self.ssh_clients_lock:
            for hostname, client in self.ssh_clients.items():
                self.logger.info(f"Closing SSH connection to {hostname}")
                client.close()
            self.ssh_clients.clear()
        
        # Clean up sandbox if configured
        if self.config.get('sandbox_enabled', True) and self.config.get('cleanup_on_shutdown', True):
            self.logger.info(f"Cleaning up sandbox directory: {self.sandbox_dir}")
            try:
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)
            except Exception as e:
                self.logger.warning(f"Error cleaning up sandbox: {str(e)}")
        
        self.is_running = False
        self.logger.info("Execution Agent stopped")
    
    def execute_step(self, task: Dict[str, Any], step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Execute a step of a task.
        
        Args:
            task: Task dictionary
            step: Step dictionary
            step_index: Index of the step
            
        Returns:
            Step execution result
        """
        self.logger.info(f"Executing step {step_index} of task {task['id']}: {step['description']}")
        
        params = step.get('parameters', {})
        
        # Determine execution type
        if 'command' in params:
            # Execute a command
            if params.get('remote', False):
                # Remote command execution
                result = self._execute_remote_command(
                    params['command'],
                    params.get('hostname'),
                    params.get('username'),
                    params.get('password'),
                    params.get('port', 22),
                    params.get('timeout', self.config.get('remote_execution', {}).get('connection_timeout', 30))
                )
            else:
                # Local command execution
                result = self._execute_local_command(
                    params['command'],
                    params.get('timeout', self.config.get('local_execution', {}).get('timeout', 300)),
                    params.get('working_dir')
                )
        
        elif 'script' in params:
            # Execute a script
            script_type = params.get('script_type', 'bash')
            
            if params.get('remote', False):
                # Remote script execution
                result = self._execute_remote_script(
                    params['script'],
                    script_type,
                    params.get('hostname'),
                    params.get('username'),
                    params.get('password'),
                    params.get('port', 22),
                    params.get('script_args', []),
                    params.get('timeout', self.config.get('remote_execution', {}).get('connection_timeout', 30))
                )
            else:
                # Local script execution
                result = self._execute_local_script(
                    params['script'],
                    script_type,
                    params.get('script_args', []),
                    params.get('timeout', self.config.get('local_execution', {}).get('timeout', 300)),
                    params.get('working_dir')
                )
        
        elif 'ansible_playbook' in params:
            # Execute an Ansible playbook
            result = self._execute_ansible_playbook(
                params['ansible_playbook'],
                params.get('inventory'),
                params.get('extra_vars', {}),
                params.get('timeout', 600)
            )
        
        else:
            # Unknown execution type
            return {
                "status": "error",
                "message": "Unknown execution type",
                "details": "The step parameters must include 'command', 'script', or 'ansible_playbook'"
            }
        
        self.logger.info(f"Step {step_index} of task {task['id']} execution completed with status: {result['status']}")
        return result
    
    def _execute_local_command(self, command: str, timeout: int = 300, 
                              working_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a command on the local system.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            working_dir: Working directory for the command
            
        Returns:
            Execution result dictionary
        """
        self.logger.info(f"Executing local command: {command}")
        
        start_time = time.time()
        
        try:
            # Validate command safety if configured
            if self.config.get('validate_commands', True):
                self._validate_command_safety(command)
            
            # Create process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir
            )
            
            # Wait for process to complete with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Get execution time
            execution_time = time.time() - start_time
            
            # Check return code
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Command executed successfully",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode,
                        "execution_time": execution_time
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Command failed with return code {process.returncode}",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode,
                        "execution_time": execution_time
                    }
                }
        
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Command timed out after {timeout} seconds: {command}")
            return {
                "status": "timeout",
                "message": f"Command timed out after {timeout} seconds",
                "details": {
                    "command": command,
                    "timeout": timeout
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing command: {str(e)}",
                "details": {
                    "command": command,
                    "exception": str(e)
                }
            }
    
    def _execute_remote_command(self, command: str, hostname: str, 
                               username: str, password: Optional[str] = None, 
                               port: int = 22, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command on a remote system via SSH.
        
        Args:
            command: Command to execute
            hostname: Remote hostname or IP
            username: SSH username
            password: SSH password (optional if using key-based authentication)
            port: SSH port
            timeout: Connection timeout in seconds
            
        Returns:
            Execution result dictionary
        """
        self.logger.info(f"Executing remote command on {hostname}: {command}")
        
        start_time = time.time()
        
        try:
            # Get or create SSH client
            client = self._get_ssh_client(hostname, username, password, port, timeout)
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command)
            
            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()
            
            # Get output
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            
            # Get execution time
            execution_time = time.time() - start_time
            
            if exit_status == 0:
                return {
                    "status": "success",
                    "message": "Command executed successfully",
                    "details": {
                        "stdout": stdout_str,
                        "stderr": stderr_str,
                        "return_code": exit_status,
                        "execution_time": execution_time
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Command failed with return code {exit_status}",
                    "details": {
                        "stdout": stdout_str,
                        "stderr": stderr_str,
                        "return_code": exit_status,
                        "execution_time": execution_time
                    }
                }
        
        except SSHException as e:
            self.logger.error(f"SSH error connecting to {hostname}: {str(e)}")
            return {
                "status": "error",
                "message": f"SSH error: {str(e)}",
                "details": {
                    "command": command,
                    "hostname": hostname,
                    "exception": str(e)
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error executing remote command: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing remote command: {str(e)}",
                "details": {
                    "command": command,
                    "hostname": hostname,
                    "exception": str(e)
                }
            }
    
    def _execute_local_script(self, script_content: str, script_type: str, 
                             script_args: List[str] = [], timeout: int = 300, 
                             working_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a script on the local system.
        
        Args:
            script_content: Content of the script
            script_type: Type of script (bash, python, etc.)
            script_args: Arguments to pass to the script
            timeout: Timeout in seconds
            working_dir: Working directory for the script
            
        Returns:
            Execution result dictionary
        """
        self.logger.info(f"Executing local {script_type} script")
        
        # Create a temporary script file
        with tempfile.NamedTemporaryFile(
            prefix="itadmin_", 
            suffix=self._get_script_extension(script_type),
            mode='w',
            delete=False
        ) as script_file:
            script_path = script_file.name
            script_file.write(script_content)
        
        try:
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Build command
            if script_type == 'python':
                command = ["python", script_path] + script_args
            elif script_type == 'bash':
                command = ["bash", script_path] + script_args
            elif script_type == 'powershell':
                command = ["powershell", "-File", script_path] + script_args
            else:
                command = [script_path] + script_args
            
            # Execute command
            start_time = time.time()
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Get execution time
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Script executed successfully",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode,
                        "execution_time": execution_time,
                        "script_type": script_type
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Script failed with return code {process.returncode}",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode,
                        "execution_time": execution_time,
                        "script_type": script_type
                    }
                }
        
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Script execution timed out after {timeout} seconds")
            return {
                "status": "timeout",
                "message": f"Script execution timed out after {timeout} seconds",
                "details": {
                    "script_type": script_type,
                    "timeout": timeout
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error executing script: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing script: {str(e)}",
                "details": {
                    "script_type": script_type,
                    "exception": str(e)
                }
            }
        
        finally:
            # Clean up the temporary file
            try:
                os.unlink(script_path)
            except Exception as e:
                self.logger.warning(f"Error removing temporary script file: {str(e)}")
    
    def _execute_remote_script(self, script_content: str, script_type: str, 
                              hostname: str, username: str, 
                              password: Optional[str] = None, port: int = 22,
                              script_args: List[str] = [], 
                              timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a script on a remote system via SSH.
        
        Args:
            script_content: Content of the script
            script_type: Type of script (bash, python, etc.)
            hostname: Remote hostname or IP
            username: SSH username
            password: SSH password (optional if using key-based authentication)
            port: SSH port
            script_args: Arguments to pass to the script
            timeout: Connection timeout in seconds
            
        Returns:
            Execution result dictionary
        """
        self.logger.info(f"Executing remote {script_type} script on {hostname}")
        
        try:
            # Get or create SSH client
            client = self._get_ssh_client(hostname, username, password, port, timeout)
            
            # Create temporary script file name on remote system
            remote_filename = f"/tmp/itadmin_{int(time.time())}_{os.urandom(4).hex()}{self._get_script_extension(script_type)}"
            
            # Create SFTP client
            sftp = client.open_sftp()
            
            # Upload script to remote system
            with sftp.file(remote_filename, 'w') as remote_file:
                remote_file.write(script_content)
            
            # Make script executable
            sftp.chmod(remote_filename, 0o755)
            
            # Build command
            if script_type == 'python':
                command = f"python {remote_filename} {' '.join(script_args)}"
            elif script_type == 'bash':
                command = f"bash {remote_filename} {' '.join(script_args)}"
            elif script_type == 'powershell':
                command = f"powershell -File {remote_filename} {' '.join(script_args)}"
            else:
                command = f"{remote_filename} {' '.join(script_args)}"
            
            # Execute command
            start_time = time.time()
            stdin, stdout, stderr = client.exec_command(command)
            
            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()
            
            # Get output
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            
            # Clean up the remote script
            sftp.remove(remote_filename)
            sftp.close()
            
            # Get execution time
            execution_time = time.time() - start_time
            
            if exit_status == 0:
                return {
                    "status": "success",
                    "message": "Script executed successfully",
                    "details": {
                        "stdout": stdout_str,
                        "stderr": stderr_str,
                        "return_code": exit_status,
                        "execution_time": execution_time,
                        "script_type": script_type
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Script failed with return code {exit_status}",
                    "details": {
                        "stdout": stdout_str,
                        "stderr": stderr_str,
                        "return_code": exit_status,
                        "execution_time": execution_time,
                        "script_type": script_type
                    }
                }
        
        except SSHException as e:
            self.logger.error(f"SSH error connecting to {hostname}: {str(e)}")
            return {
                "status": "error",
                "message": f"SSH error: {str(e)}",
                "details": {
                    "hostname": hostname,
                    "exception": str(e)
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error executing remote script: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing remote script: {str(e)}",
                "details": {
                    "hostname": hostname,
                    "exception": str(e)
                }
            }
    
    def _execute_ansible_playbook(self, playbook_content: str, 
                                 inventory: Optional[str] = None,
                                 extra_vars: Dict[str, Any] = {},
                                 timeout: int = 600) -> Dict[str, Any]:
        """
        Execute an Ansible playbook.
        
        Args:
            playbook_content: Content of the Ansible playbook
            inventory: Inventory string or path to inventory file
            extra_vars: Extra variables to pass to Ansible
            timeout: Timeout in seconds
            
        Returns:
            Execution result dictionary
        """
        self.logger.info("Executing Ansible playbook")
        
        try:
            # Create temporary directory for Ansible files
            temp_dir = tempfile.mkdtemp(prefix="itadmin_ansible_")
            
            # Create playbook file
            playbook_path = os.path.join(temp_dir, "playbook.yml")
            with open(playbook_path, 'w') as f:
                f.write(playbook_content)
            
            # Create inventory file if provided
            inventory_path = None
            if inventory:
                inventory_path = os.path.join(temp_dir, "inventory")
                with open(inventory_path, 'w') as f:
                    f.write(inventory)
            
            # Create vars file if provided
            vars_path = None
            if extra_vars:
                vars_path = os.path.join(temp_dir, "vars.json")
                with open(vars_path, 'w') as f:
                    json.dump(extra_vars, f)
            
            # Build ansible-playbook command
            command = ["ansible-playbook", playbook_path]
            
            if inventory_path:
                command.extend(["-i", inventory_path])
            
            if vars_path:
                command.extend(["--extra-vars", f"@{vars_path}"])
            
            # Execute command
            start_time = time.time()
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Get execution time
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Ansible playbook executed successfully",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode,
                        "execution_time": execution_time
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ansible playbook failed with return code {process.returncode}",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": process.returncode,
                        "execution_time": execution_time
                    }
                }
        
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Ansible playbook execution timed out after {timeout} seconds")
            return {
                "status": "timeout",
                "message": f"Ansible playbook execution timed out after {timeout} seconds",
                "details": {
                    "timeout": timeout
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error executing Ansible playbook: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing Ansible playbook: {str(e)}",
                "details": {
                    "exception": str(e)
                }
            }
        
        finally:
            # Clean up the temporary directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                self.logger.warning(f"Error removing temporary Ansible directory: {str(e)}")
    
    def _get_ssh_client(self, hostname: str, username: str, 
                       password: Optional[str] = None, port: int = 22, 
                       timeout: int = 30) -> paramiko.SSHClient:
        """
        Get or create an SSH client for a remote host.
        
        Args:
            hostname: Remote hostname or IP
            username: SSH username
            password: SSH password (optional if using key-based authentication)
            port: SSH port
            timeout: Connection timeout in seconds
            
        Returns:
            Paramiko SSH client
            
        Raises:
            SSHException: If unable to connect
        """
        client_key = f"{username}@{hostname}:{port}"
        
        with self.ssh_clients_lock:
            if client_key in self.ssh_clients:
                # Check if the connection is still active
                client = self.ssh_clients[client_key]
                transport = client.get_transport()
                if transport and transport.is_active():
                    return client
                
                # Connection is not active, remove it
                self.logger.info(f"SSH connection to {hostname} is not active, creating a new one")
                client.close()
                self.ssh_clients.pop(client_key)
        
        # Create a new client
        self.logger.info(f"Creating new SSH connection to {hostname}")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                allow_agent=True,
                look_for_keys=True
            )
            
            with self.ssh_clients_lock:
                self.ssh_clients[client_key] = client
            
            return client
        
        except Exception as e:
            # Close the client if connection failed
            client.close()
            raise SSHException(f"Failed to connect to {hostname}: {str(e)}")
    
    def _validate_command_safety(self, command: str) -> None:
        """
        Validate that a command is safe to execute.
        
        This is a simple implementation that checks for dangerous patterns.
        A more sophisticated implementation could use a whitelist or a parser.
        
        Args:
            command: Command to validate
            
        Raises:
            ValueError: If the command is deemed unsafe
        """
        # List of dangerous patterns
        dangerous_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "> /dev/sda",
            "mkfs",
            ":(){:|:&};:",
            "dd if=/dev/random",
            "mv /* /dev/null"
        ]
        
        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if pattern in command:
                self.logger.warning(f"Dangerous command detected: {command}")
                raise ValueError(f"Dangerous command pattern detected: {pattern}")
    
    @staticmethod
    def _get_script_extension(script_type: str) -> str:
        """
        Get the file extension for a script type.
        
        Args:
            script_type: Type of script (bash, python, etc.)
            
        Returns:
            File extension for the script type
        """
        if script_type == 'python':
            return '.py'
        elif script_type == 'bash':
            return '.sh'
        elif script_type == 'powershell':
            return '.ps1'
        else:
            return '.script' 