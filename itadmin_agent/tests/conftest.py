"""
Pytest configuration file.

This file contains test fixtures and configuration for the IT Admin Agent test suite.
"""
import os
import sys
import tempfile
import pytest
import yaml
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_config():
    """
    Create a test configuration.
    
    This fixture provides a minimal configuration dictionary suitable for testing.
    """
    config = {
        "system": {
            "name": "IT Admin Agent",
            "version": "0.1.0-test",
            "log_level": "ERROR",
            "environment": "testing"
        },
        "agents": {
            "task_manager": {
                "enabled": True,
                "max_concurrent_tasks": 2
            },
            "diagnostics": {
                "enabled": True
            },
            "execution": {
                "enabled": True,
                "sandbox_enabled": True
            },
            "learning": {
                "enabled": True
            },
            "validation": {
                "enabled": True,
                "strict_mode": False
            }
        },
        "knowledge_base": {
            "vector_db": {
                "type": "memory",
                "embedding_model": "test-embeddings",
                "dimension": 128
            },
            "relational_db": {
                "type": "sqlite",
                "path": ":memory:",
                "backup_enabled": False
            }
        },
        "task_planner": {
            "llm": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.2,
                "max_tokens": 500
            },
            "default_checks": []
        },
        "execution": {
            "sandbox": {
                "enabled": True,
                "isolation_level": "process"
            },
            "local_execution": {
                "timeout": 10,
                "allowed_directories": ["./tests/scripts"]
            }
        },
        "security": {
            "authentication": {
                "enabled": False
            }
        },
        "human_interaction": {
            "default_mode": "autonomous"
        },
        "monitoring": {
            "logging": {
                "file_path": "./logs"
            }
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8081
        }
    }
    return config


@pytest.fixture
def temp_config_file(test_config):
    """
    Create a temporary config file.
    
    This fixture writes the test configuration to a temporary YAML file.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.safe_dump(test_config, f)
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Clean up the temporary file
    os.unlink(temp_file_path)
