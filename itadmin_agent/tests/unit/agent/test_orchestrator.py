"""
Tests for the Agent Orchestrator.

This module contains unit tests for the Agent Orchestrator class.
"""
import pytest
from unittest.mock import MagicMock, patch
import threading
import time
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parents[3]))

from agent.orchestrator import AgentOrchestrator, TaskStatus


class TestAgentOrchestrator:
    """Test suite for the Agent Orchestrator."""
    
    def test_init(self):
        """Test initialization of the orchestrator."""
        config = {
            "system": {"name": "IT Admin Agent", "version": "0.1.0", "log_level": "INFO"},
            "agents": {
                "task_manager": {"enabled": True},
                "diagnostics": {"enabled": True},
                "execution": {"enabled": True},
                "learning": {"enabled": True},
                "validation": {"enabled": True}
            }
        }
        
        orchestrator = AgentOrchestrator(config)
        
        assert orchestrator.config == config
        assert not orchestrator.is_running
        assert isinstance(orchestrator.shutdown_flag, threading.Event)
        assert isinstance(orchestrator.tasks, dict)
    
    def test_start_stop(self):
        """Test starting and stopping the orchestrator."""
        config = {
            "system": {"name": "IT Admin Agent", "version": "0.1.0", "log_level": "INFO"},
            "agents": {
                "task_manager": {"enabled": True},
                "diagnostics": {"enabled": True},
                "execution": {"enabled": True},
                "learning": {"enabled": True},
                "validation": {"enabled": True}
            }
        }
        
        # Create mock agents
        mock_task_manager = MagicMock()
        mock_diagnostics = MagicMock()
        mock_execution = MagicMock()
        mock_learning = MagicMock()
        mock_validation = MagicMock()
        
        with patch('agent.orchestrator.TaskManagerAgent', return_value=mock_task_manager), \
             patch('agent.orchestrator.DiagnosticsAgent', return_value=mock_diagnostics), \
             patch('agent.orchestrator.ExecutionAgent', return_value=mock_execution), \
             patch('agent.orchestrator.LearningAgent', return_value=mock_learning), \
             patch('agent.orchestrator.ValidationAgent', return_value=mock_validation):
            
            orchestrator = AgentOrchestrator(config)
            
            # Test start
            orchestrator.start()
            assert orchestrator.is_running
            mock_task_manager.start.assert_called_once()
            mock_diagnostics.start.assert_called_once()
            mock_execution.start.assert_called_once()
            mock_learning.start.assert_called_once()
            mock_validation.start.assert_called_once()
            
            # Test stop
            orchestrator.stop()
            assert not orchestrator.is_running
            mock_task_manager.stop.assert_called_once()
            mock_diagnostics.stop.assert_called_once()
            mock_execution.stop.assert_called_once()
            mock_learning.stop.assert_called_once()
            mock_validation.stop.assert_called_once()
    
    def test_create_task(self):
        """Test creating a task."""
        config = {
            "system": {"name": "IT Admin Agent", "version": "0.1.0", "log_level": "INFO"},
            "agents": {
                "task_manager": {"enabled": True},
                "diagnostics": {"enabled": True},
                "execution": {"enabled": True},
                "learning": {"enabled": True},
                "validation": {"enabled": True}
            }
        }
        
        orchestrator = AgentOrchestrator(config)
        
        # Create a task
        task_id = orchestrator.create_task(
            task_type="test_task",
            description="Test task description",
            parameters={"param1": "value1"},
            priority="high"
        )
        
        # Verify task was created correctly
        assert task_id in orchestrator.tasks
        task = orchestrator.tasks[task_id]
        assert task["type"] == "test_task"
        assert task["description"] == "Test task description"
        assert task["parameters"] == {"param1": "value1"}
        assert task["priority"] == "high"
        assert task["status"] == TaskStatus.PENDING.value
        assert "created_at" in task
        assert isinstance(task["steps"], list)
        assert len(task["steps"]) == 0
    
    def test_get_task(self):
        """Test retrieving a task."""
        config = {
            "system": {"name": "IT Admin Agent", "version": "0.1.0", "log_level": "INFO"},
            "agents": {
                "task_manager": {"enabled": True},
                "diagnostics": {"enabled": True},
                "execution": {"enabled": True},
                "learning": {"enabled": True},
                "validation": {"enabled": True}
            }
        }
        
        orchestrator = AgentOrchestrator(config)
        
        # Create a task
        task_id = orchestrator.create_task(
            task_type="test_task",
            description="Test task description",
            parameters={"param1": "value1"}
        )
        
        # Retrieve the task
        task = orchestrator.get_task(task_id)
        
        # Verify task was retrieved correctly
        assert task["id"] == task_id
        assert task["type"] == "test_task"
        assert task["description"] == "Test task description"
        
        # Test non-existent task
        with pytest.raises(ValueError):
            orchestrator.get_task("non-existent-id")
            
    def test_update_task_status(self):
        """Test updating a task status."""
        config = {
            "system": {"name": "IT Admin Agent", "version": "0.1.0", "log_level": "INFO"},
            "agents": {
                "task_manager": {"enabled": True},
                "diagnostics": {"enabled": True},
                "execution": {"enabled": True},
                "learning": {"enabled": True},
                "validation": {"enabled": True}
            }
        }
        
        orchestrator = AgentOrchestrator(config)
        
        # Create a task
        task_id = orchestrator.create_task(
            task_type="test_task",
            description="Test task description"
        )
        
        # Update status
        orchestrator.update_task_status(task_id, TaskStatus.EXECUTING.value)
        
        # Verify status was updated
        task = orchestrator.get_task(task_id)
        assert task["status"] == TaskStatus.EXECUTING.value
        
        # Test invalid status
        with pytest.raises(ValueError):
            orchestrator.update_task_status(task_id, "invalid_status") 