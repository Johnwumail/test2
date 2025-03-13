#!/usr/bin/env python3
"""
Database Initialization Utility

This module initializes the databases used by the IT Admin Agent system.
It creates the necessary directory structure, sets up the SQLite database,
and initializes the vector database collections.
"""
import os
import sys
import argparse
import logging
import sqlite3
from pathlib import Path

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from utils.config_loader import ConfigLoader
from utils.logging_setup import setup_logging


def initialize_relational_db(config, force=False):
    """
    Initialize the SQLite database.
    
    Args:
        config: Configuration dictionary
        force: Whether to force reinitialization
    
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Get database path
    db_config = config['knowledge_base']['relational_db']
    db_path = Path(db_config['path'])
    
    # Create directory if it doesn't exist
    os.makedirs(db_path.parent, exist_ok=True)
    
    # Check if database already exists
    if db_path.exists() and not force:
        logger.warning(f"Database already exists at {db_path}. Use --force to reinitialize.")
        return False
    
    # Connect to database (creates it if it doesn't exist)
    logger.info(f"Initializing SQLite database at {db_path}")
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.cursor()
        
        # Create tasks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            parameters TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            result TEXT,
            error TEXT
        )
        ''')
        
        # Create task_steps table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            result TEXT,
            error TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
        ''')
        
        # Create scripts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT NOT NULL,
            tags TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Create known_errors table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS known_errors (
            id TEXT PRIMARY KEY,
            error_message TEXT NOT NULL,
            solution TEXT NOT NULL,
            tags TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Create servers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id TEXT PRIMARY KEY,
            hostname TEXT NOT NULL,
            ip_address TEXT,
            os_type TEXT,
            os_version TEXT,
            status TEXT NOT NULL,
            last_seen TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Create server_configs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_configs (
            id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            config_type TEXT NOT NULL,
            config_name TEXT NOT NULL,
            content TEXT NOT NULL,
            active BOOLEAN NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (server_id) REFERENCES servers (id)
        )
        ''')
        
        conn.commit()
        logger.info("SQLite database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {str(e)}", exc_info=True)
        return False
        
    finally:
        conn.close()


def initialize_vector_db(config, force=False):
    """
    Initialize the vector database.
    
    Args:
        config: Configuration dictionary
        force: Whether to force reinitialization
    
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Get vector database path
    vector_db_config = config['knowledge_base']['vector_db']
    vector_db_path = Path(vector_db_config['path'])
    
    # Create directory if it doesn't exist
    os.makedirs(vector_db_path, exist_ok=True)
    
    # Check if vector database is already initialized
    if list(vector_db_path.glob("*")) and not force:
        logger.warning(f"Vector database directory at {vector_db_path} is not empty. Use --force to reinitialize.")
        return False
    
    logger.info(f"Vector database directory prepared at {vector_db_path}")
    logger.info("Vector collections will be created on first use")
    
    return True


def initialize_databases(config_path, force=False):
    """
    Initialize all databases.
    
    Args:
        config_path: Path to configuration file
        force: Whether to force reinitialization
    
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting database initialization")
    
    try:
        # Load configuration
        config = ConfigLoader.load(Path(config_path))
        
        # Create data directory
        data_dir = Path(parent_dir) / "data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize relational database
        if not initialize_relational_db(config, force):
            return False
        
        # Initialize vector database
        if not initialize_vector_db(config, force):
            return False
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing databases: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Initialize IT Admin Agent databases")
    parser.add_argument(
        "--config", 
        type=str, 
        default="../config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force reinitialization of existing databases"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_dir = Path(parent_dir) / "logs"
    os.makedirs(log_dir, exist_ok=True)
    setup_logging(args.log_level, log_dir)
    
    # Initialize databases
    success = initialize_databases(args.config, args.force)
    
    if success:
        print("Database initialization completed successfully.")
        return 0
    else:
        print("Database initialization failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 