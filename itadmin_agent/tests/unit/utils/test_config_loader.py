"""
Tests for the Config Loader utility.

This module contains unit tests for the ConfigLoader class.
"""
import os
import pytest
from pathlib import Path
import tempfile
import yaml
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parents[3]))

from utils.config_loader import ConfigLoader, ConfigValidationError


class TestConfigLoader:
    """Test suite for the Config Loader."""
    
    def test_load_valid_config(self):
        """Test loading a valid config file."""
        # Create a temporary config file
        test_config = {
            "system": {
                "name": "IT Admin Agent",
                "version": "0.1.0-test",
                "log_level": "INFO",
                "environment": "testing"
            },
            "agents": {
                "task_manager": {"enabled": True}
            },
            "knowledge_base": {
                "vector_db": {"type": "memory"},
                "relational_db": {"type": "sqlite"}
            },
            "task_planner": {
                "llm": {"model": "gpt-3.5-turbo"}
            },
            "execution": {},
            "security": {},
            "human_interaction": {},
            "monitoring": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(test_config, f)
            temp_file_path = f.name
        
        try:
            # Load the config
            config = ConfigLoader.load(Path(temp_file_path))
            
            # Verify the config was loaded correctly
            assert config["system"]["name"] == "IT Admin Agent"
            assert config["system"]["version"] == "0.1.0-test"
            assert config["system"]["log_level"] == "INFO"
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    
    def test_load_missing_file(self):
        """Test loading a non-existent config file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load(Path("non_existent_config.yaml"))
    
    def test_validate_missing_section(self):
        """Test validating a config with missing required sections."""
        # Create a config missing required sections
        invalid_config = {
            "system": {
                "name": "IT Admin Agent",
                "version": "0.1.0",
                "log_level": "INFO",
                "environment": "testing"
            }
            # Missing other required sections
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            temp_file_path = f.name
        
        try:
            # Attempt to load the config, which should trigger validation
            with pytest.raises(ConfigValidationError):
                ConfigLoader.load(Path(temp_file_path))
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    
    def test_environment_override(self):
        """Test environment-specific config overrides."""
        # Create a base config
        base_config = {
            "system": {
                "name": "IT Admin Agent",
                "version": "0.1.0",
                "log_level": "INFO",
                "environment": "testing"
            },
            "agents": {"task_manager": {"enabled": True}},
            "knowledge_base": {"vector_db": {"type": "memory"}, "relational_db": {"type": "sqlite"}},
            "task_planner": {"llm": {"model": "gpt-3.5-turbo"}},
            "execution": {},
            "security": {},
            "human_interaction": {},
            "monitoring": {}
        }
        
        # Create an environment-specific config
        env_config = {
            "system": {"log_level": "DEBUG"},
            "agents": {"task_manager": {"max_concurrent_tasks": 10}}
        }
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "config.yaml"
            env_path = Path(temp_dir) / "config.testing.yaml"
            
            with open(base_path, 'w') as f:
                yaml.safe_dump(base_config, f)
            
            with open(env_path, 'w') as f:
                yaml.safe_dump(env_config, f)
            
            # Load the config
            config = ConfigLoader.load(base_path)
            
            # Verify base values
            assert config["system"]["name"] == "IT Admin Agent"
            assert config["system"]["version"] == "0.1.0"
            
            # Verify overridden values
            assert config["system"]["log_level"] == "DEBUG"
            assert config["agents"]["task_manager"]["max_concurrent_tasks"] == 10
    
    def test_env_var_overrides(self):
        """Test environment variable overrides."""
        # Create a base config
        base_config = {
            "system": {
                "name": "IT Admin Agent",
                "version": "0.1.0",
                "log_level": "INFO",
                "environment": "testing"
            },
            "agents": {"task_manager": {"enabled": True}},
            "knowledge_base": {"vector_db": {"type": "memory"}, "relational_db": {"type": "sqlite"}},
            "task_planner": {"llm": {"model": "gpt-3.5-turbo"}},
            "execution": {},
            "security": {},
            "human_interaction": {},
            "monitoring": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(base_config, f)
            temp_file_path = f.name
        
        try:
            # Set environment variables to override config
            os.environ["ITADMIN_SYSTEM_LOG_LEVEL"] = "DEBUG"
            os.environ["ITADMIN_AGENTS_TASK_MANAGER_MAX_CONCURRENT_TASKS"] = "15"
            
            # Load the config
            config = ConfigLoader.load(Path(temp_file_path))
            
            # Verify base values
            assert config["system"]["name"] == "IT Admin Agent"
            assert config["system"]["version"] == "0.1.0"
            
            # Verify overridden values
            assert config["system"]["log_level"] == "DEBUG"
            assert config["agents"]["task_manager"]["max_concurrent_tasks"] == 15
            
            # Clean up
            del os.environ["ITADMIN_SYSTEM_LOG_LEVEL"]
            del os.environ["ITADMIN_AGENTS_TASK_MANAGER_MAX_CONCURRENT_TASKS"]
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    
    def test_deep_merge(self):
        """Test deep merging of dictionaries."""
        base = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            },
            "e": [1, 2, 3]
        }
        
        override = {
            "b": {
                "c": 4,
                "f": 5
            },
            "g": 6
        }
        
        result = ConfigLoader._deep_merge(base, override)
        
        assert result["a"] == 1
        assert result["b"]["c"] == 4  # Overridden
        assert result["b"]["d"] == 3  # Preserved
        assert result["b"]["f"] == 5  # Added
        assert result["e"] == [1, 2, 3]  # Preserved
        assert result["g"] == 6  # Added 