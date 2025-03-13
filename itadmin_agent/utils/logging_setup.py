"""
Logging Setup Utility

This module handles setting up logging for the IT Admin Agent system.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str, log_dir: Path) -> None:
    """
    Set up logging for the application.
    
    Args:
        log_level: The log level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Set up file handler with daily rotation
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_dir / f"itadmin_{today}.log"
    
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        backupCount=30  # Keep logs for 30 days
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Log initial message
    root_logger.info(f"Logging initialized at level {log_level}")
    
    # Configure library loggers to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    
    # Add a null handler to the application logger to avoid "No handler found" warnings
    logging.getLogger('itadmin').addHandler(logging.NullHandler())


def get_task_logger(task_id: str) -> logging.Logger:
    """
    Get a logger for a specific task with proper configuration.
    
    Args:
        task_id: The ID of the task
        
    Returns:
        A configured logger for the task
    """
    logger = logging.getLogger(f"itadmin.task.{task_id}")
    return logger


def get_agent_logger(agent_type: str) -> logging.Logger:
    """
    Get a logger for a specific agent type with proper configuration.
    
    Args:
        agent_type: The type of agent (e.g., 'task_manager', 'execution')
        
    Returns:
        A configured logger for the agent
    """
    logger = logging.getLogger(f"itadmin.agent.{agent_type}")
    return logger 