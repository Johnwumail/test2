"""
Configuration Loader Utility

This module handles loading and validating configuration files for the IT Admin Agent system.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""
    pass


class ConfigLoader:
    """Utility class for loading and validating configuration files."""
    
    @staticmethod
    def load(config_path: Path) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary containing configuration settings
            
        Raises:
            FileNotFoundError: If the configuration file does not exist
            ConfigValidationError: If the configuration is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            try:
                config = yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise ConfigValidationError(f"Invalid YAML in configuration file: {e}")
        
        # Validate the configuration
        ConfigLoader._validate_config(config)
        
        # Load environment-specific overrides if available
        env = config.get('system', {}).get('environment', 'development')
        env_config_path = config_path.parent / f"config.{env}.yaml"
        
        if env_config_path.exists():
            with open(env_config_path, 'r') as file:
                try:
                    env_config = yaml.safe_load(file)
                    # Merge environment-specific configuration
                    config = ConfigLoader._deep_merge(config, env_config)
                except yaml.YAMLError as e:
                    raise ConfigValidationError(f"Invalid YAML in environment configuration file: {e}")
        
        # Apply environment variable overrides
        config = ConfigLoader._apply_env_overrides(config)
        
        return config
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """
        Validate the configuration structure.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigValidationError: If the configuration is invalid
        """
        # Required top-level sections
        required_sections = [
            'system', 'agents', 'knowledge_base', 'task_planner', 
            'execution', 'security', 'human_interaction', 'monitoring'
        ]
        
        for section in required_sections:
            if section not in config:
                raise ConfigValidationError(f"Missing required configuration section: {section}")
        
        # Validate system section
        system = config['system']
        if not isinstance(system, dict):
            raise ConfigValidationError("'system' section must be a dictionary")
            
        required_system_keys = ['name', 'version', 'log_level', 'environment']
        for key in required_system_keys:
            if key not in system:
                raise ConfigValidationError(f"Missing required key in 'system' section: {key}")
        
        # Additional validation can be added for other sections as needed
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Dictionary with override values
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    @staticmethod
    def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to the configuration.
        
        Environment variables should follow the pattern:
        ITADMIN_SECTION_SUBSECTION_KEY=value
        
        For example:
        ITADMIN_SYSTEM_LOG_LEVEL=DEBUG
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with environment variable overrides applied
        """
        result = config.copy()
        
        for env_var, value in os.environ.items():
            if env_var.startswith('ITADMIN_'):
                # Remove the prefix and split by underscore
                parts = env_var[8:].lower().split('_')
                
                if len(parts) >= 2:
                    # Navigate to the correct location in the config
                    current = result
                    for i, part in enumerate(parts[:-1]):
                        if part not in current:
                            current[part] = {}
                        elif not isinstance(current[part], dict):
                            # If the path exists but is not a dict, convert it
                            current[part] = {}
                        current = current[part]
                    
                    # Set the value for the final key
                    try:
                        # Try to convert to appropriate type (int, float, bool)
                        if value.lower() in ('true', 'yes', 'on'):
                            current[parts[-1]] = True
                        elif value.lower() in ('false', 'no', 'off'):
                            current[parts[-1]] = False
                        elif value.isdigit():
                            current[parts[-1]] = int(value)
                        elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                            current[parts[-1]] = float(value)
                        else:
                            current[parts[-1]] = value
                    except Exception:
                        # If conversion fails, use the string value
                        current[parts[-1]] = value
        
        return result 