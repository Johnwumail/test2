"""
Knowledge Base

This module implements the knowledge base for the IT Admin Agent system,
storing and retrieving information about tasks, solutions, and system configurations.
"""
import os
import json
import time
import logging
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import uuid
from datetime import datetime

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from utils.logging_setup import get_agent_logger


class KnowledgeBase:
    """
    Knowledge Base for the IT Admin Agent system.
    
    This class is responsible for:
    - Storing and retrieving task information
    - Maintaining a vector database for semantic search
    - Storing and retrieving system configuration information
    - Learning from successful tasks
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Knowledge Base.
        
        Args:
            config: Configuration dictionary for the knowledge base
        """
        self.logger = get_agent_logger("knowledge_base")
        self.logger.info("Initializing Knowledge Base")
        
        self.config = config
        
        # Set up vector database
        self._setup_vector_db()
        
        # Set up relational database
        self._setup_relational_db()
        
        self.logger.info("Knowledge Base initialization complete")
    
    def _setup_vector_db(self) -> None:
        """Set up the vector database for semantic search."""
        vector_db_config = self.config['vector_db']
        
        # Create the directory if it doesn't exist
        vector_db_path = Path(vector_db_config['path'])
        os.makedirs(vector_db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.logger.info(f"Initializing vector database at {vector_db_path}")
        self.vector_client = chromadb.PersistentClient(
            path=str(vector_db_path),
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Set up embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model_name=vector_db_config.get('embedding_model', 'text-embedding-ada-002')
        )
        
        # Create or get collections
        self.tasks_collection = self._get_or_create_collection("tasks")
        self.scripts_collection = self._get_or_create_collection("scripts")
        self.configs_collection = self._get_or_create_collection("configs")
        self.errors_collection = self._get_or_create_collection("errors")
        
        self.logger.info("Vector database setup complete")
    
    def _get_or_create_collection(self, name: str) -> Any:
        """
        Get or create a ChromaDB collection.
        
        Args:
            name: Name of the collection
            
        Returns:
            ChromaDB collection
        """
        try:
            collection = self.vector_client.get_collection(
                name=name,
                embedding_function=self.embedding_function
            )
            self.logger.info(f"Retrieved existing collection: {name}")
        except Exception:
            collection = self.vector_client.create_collection(
                name=name,
                embedding_function=self.embedding_function
            )
            self.logger.info(f"Created new collection: {name}")
            
        return collection
    
    def _setup_relational_db(self) -> None:
        """Set up the relational database for structured data."""
        db_config = self.config['relational_db']
        
        # Create directory for SQLite database if needed
        db_path = Path(db_config['path'])
        os.makedirs(db_path.parent, exist_ok=True)
        
        self.logger.info(f"Initializing relational database at {db_path}")
        
        # Connect to the database
        self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.db_conn.row_factory = sqlite3.Row
        
        # Create tables if they don't exist
        self._create_tables()
        
        self.logger.info("Relational database setup complete")
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.db_conn.cursor()
        
        # Tasks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            parameters TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            result TEXT,
            error TEXT
        )
        ''')
        
        # Task steps table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_steps (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            step_index INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            result TEXT,
            error TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
        ''')
        
        # Scripts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            tags TEXT
        )
        ''')
        
        # Server configurations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_configs (
            id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            config_type TEXT NOT NULL,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Known errors table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS known_errors (
            id TEXT PRIMARY KEY,
            error_message TEXT NOT NULL,
            solution TEXT NOT NULL,
            context TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            frequency INTEGER DEFAULT 1
        )
        ''')
        
        # Servers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id TEXT PRIMARY KEY,
            hostname TEXT NOT NULL,
            ip_address TEXT,
            os_type TEXT,
            os_version TEXT,
            role TEXT,
            status TEXT,
            last_check TEXT,
            metadata TEXT
        )
        ''')
        
        self.db_conn.commit()
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """
        Add a task to the knowledge base.
        
        Args:
            task: Task dictionary
        """
        self.logger.info(f"Adding task to knowledge base: {task['id']}")
        
        # Add to relational database
        cursor = self.db_conn.cursor()
        cursor.execute(
            '''
            INSERT INTO tasks 
            (id, type, description, parameters, status, created_at, completed_at, result, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                task['id'],
                task['type'],
                task['description'],
                json.dumps(task['parameters']),
                task['status'],
                task['created_at'],
                task.get('completed_at'),
                json.dumps(task.get('result')) if task.get('result') else None,
                task.get('error')
            )
        )
        
        # Add steps if present
        for i, step in enumerate(task.get('steps', [])):
            step_id = str(uuid.uuid4())
            cursor.execute(
                '''
                INSERT INTO task_steps
                (id, task_id, step_index, description, status, created_at, completed_at, result, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    step_id,
                    task['id'],
                    i,
                    step['description'],
                    step['status'],
                    step['created_at'],
                    step.get('completed_at'),
                    json.dumps(step.get('result')) if step.get('result') else None,
                    step.get('error')
                )
            )
        
        self.db_conn.commit()
        
        # Add to vector database for semantic search
        # Create a rich text representation for embedding
        task_text = f"""
        Task ID: {task['id']}
        Type: {task['type']}
        Description: {task['description']}
        Status: {task['status']}
        Parameters: {json.dumps(task['parameters'])}
        
        Steps:
        {self._format_steps_for_embedding(task.get('steps', []))}
        
        Result: {json.dumps(task.get('result')) if task.get('result') else 'None'}
        Error: {task.get('error', 'None')}
        """
        
        # Store in vector database
        metadata = {
            'id': task['id'],
            'type': task['type'],
            'status': task['status'],
            'created_at': task['created_at']
        }
        
        self.tasks_collection.add(
            ids=[task['id']],
            documents=[task_text.strip()],
            metadatas=[metadata]
        )
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """
        Update a task in the knowledge base.
        
        Args:
            task_id: ID of the task to update
            updates: Dictionary of fields to update
        """
        self.logger.info(f"Updating task in knowledge base: {task_id}")
        
        # Update in relational database
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if key in ['parameters', 'result']:
                set_clauses.append(f"{key} = ?")
                params.append(json.dumps(value))
            elif key != 'steps':  # Steps are handled separately
                set_clauses.append(f"{key} = ?")
                params.append(value)
        
        if set_clauses:
            query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
            params.append(task_id)
            
            cursor = self.db_conn.cursor()
            cursor.execute(query, params)
        
        # Update steps if present
        if 'steps' in updates:
            for i, step in enumerate(updates['steps']):
                # Check if step exists
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "SELECT id FROM task_steps WHERE task_id = ? AND step_index = ?",
                    (task_id, i)
                )
                result = cursor.fetchone()
                
                step_data = (
                    step.get('description', ''),
                    step.get('status', 'pending'),
                    step.get('created_at', self._get_timestamp()),
                    step.get('completed_at'),
                    json.dumps(step.get('result')) if step.get('result') else None,
                    step.get('error')
                )
                
                if result:
                    # Update existing step
                    cursor.execute(
                        '''
                        UPDATE task_steps
                        SET description = ?, status = ?, created_at = ?, completed_at = ?, 
                            result = ?, error = ?
                        WHERE task_id = ? AND step_index = ?
                        ''',
                        (*step_data, task_id, i)
                    )
                else:
                    # Insert new step
                    step_id = str(uuid.uuid4())
                    cursor.execute(
                        '''
                        INSERT INTO task_steps
                        (id, task_id, step_index, description, status, created_at, 
                         completed_at, result, error)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (step_id, task_id, i, *step_data)
                    )
        
        self.db_conn.commit()
        
        # Update in vector database
        # First, get the full task to create the updated embedding
        task = self.get_task(task_id)
        if task:
            # Remove the old vector
            self.tasks_collection.delete(ids=[task_id])
            
            # Add updated vector
            task_text = f"""
            Task ID: {task['id']}
            Type: {task['type']}
            Description: {task['description']}
            Status: {task['status']}
            Parameters: {json.dumps(task['parameters'])}
            
            Steps:
            {self._format_steps_for_embedding(task.get('steps', []))}
            
            Result: {json.dumps(task.get('result')) if task.get('result') else 'None'}
            Error: {task.get('error', 'None')}
            """
            
            metadata = {
                'id': task['id'],
                'type': task['type'],
                'status': task['status'],
                'created_at': task['created_at']
            }
            
            self.tasks_collection.add(
                ids=[task_id],
                documents=[task_text.strip()],
                metadatas=[metadata]
            )
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task from the knowledge base.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task dictionary or None if not found
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        task = dict(result)
        
        # Parse JSON fields
        task['parameters'] = json.loads(task['parameters']) if task['parameters'] else {}
        task['result'] = json.loads(task['result']) if task['result'] else None
        
        # Get steps
        cursor.execute(
            "SELECT * FROM task_steps WHERE task_id = ? ORDER BY step_index",
            (task_id,)
        )
        steps = []
        for step_row in cursor.fetchall():
            step = dict(step_row)
            step['result'] = json.loads(step['result']) if step['result'] else None
            steps.append(step)
        
        task['steps'] = steps
        
        return task
    
    def search_similar_tasks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for tasks similar to the query.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of task dictionaries
        """
        self.logger.info(f"Searching for tasks similar to: {query}")
        
        # Search in vector database
        results = self.tasks_collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        # Get full task details from relational database
        tasks = []
        if results and results['ids'] and results['ids'][0]:
            for task_id in results['ids'][0]:
                task = self.get_task(task_id)
                if task:
                    tasks.append(task)
        
        return tasks
    
    def add_script(self, script: Dict[str, Any]) -> str:
        """
        Add a script to the knowledge base.
        
        Args:
            script: Script dictionary with name, description, content, and language
            
        Returns:
            Script ID
        """
        script_id = str(uuid.uuid4())
        now = self._get_timestamp()
        
        self.logger.info(f"Adding script to knowledge base: {script['name']}")
        
        # Add to relational database
        cursor = self.db_conn.cursor()
        cursor.execute(
            '''
            INSERT INTO scripts
            (id, name, description, content, language, created_at, updated_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                script_id,
                script['name'],
                script.get('description', ''),
                script['content'],
                script['language'],
                now,
                now,
                json.dumps(script.get('tags', []))
            )
        )
        
        self.db_conn.commit()
        
        # Add to vector database for semantic search
        script_text = f"""
        Script Name: {script['name']}
        Description: {script.get('description', '')}
        Language: {script['language']}
        Tags: {', '.join(script.get('tags', []))}
        
        Content:
        {script['content']}
        """
        
        metadata = {
            'id': script_id,
            'name': script['name'],
            'language': script['language'],
            'created_at': now
        }
        
        self.scripts_collection.add(
            ids=[script_id],
            documents=[script_text.strip()],
            metadatas=[metadata]
        )
        
        return script_id
    
    def search_scripts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for scripts matching the query.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of script dictionaries
        """
        self.logger.info(f"Searching for scripts matching: {query}")
        
        # Search in vector database
        results = self.scripts_collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        # Get full script details from relational database
        scripts = []
        if results and results['ids'] and results['ids'][0]:
            cursor = self.db_conn.cursor()
            for script_id in results['ids'][0]:
                cursor.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
                script_row = cursor.fetchone()
                
                if script_row:
                    script = dict(script_row)
                    script['tags'] = json.loads(script['tags']) if script['tags'] else []
                    scripts.append(script)
        
        return scripts
    
    def add_known_error(self, error: Dict[str, Any]) -> str:
        """
        Add a known error and its solution to the knowledge base.
        
        Args:
            error: Error dictionary with error_message, solution, and context
            
        Returns:
            Error ID
        """
        error_id = str(uuid.uuid4())
        now = self._get_timestamp()
        
        self.logger.info(f"Adding known error to knowledge base")
        
        # Add to relational database
        cursor = self.db_conn.cursor()
        cursor.execute(
            '''
            INSERT INTO known_errors
            (id, error_message, solution, context, created_at, updated_at, frequency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                error_id,
                error['error_message'],
                error['solution'],
                error.get('context', ''),
                now,
                now,
                1
            )
        )
        
        self.db_conn.commit()
        
        # Add to vector database for semantic search
        error_text = f"""
        Error: {error['error_message']}
        Context: {error.get('context', '')}
        Solution: {error['solution']}
        """
        
        metadata = {
            'id': error_id,
            'created_at': now
        }
        
        self.errors_collection.add(
            ids=[error_id],
            documents=[error_text.strip()],
            metadatas=[metadata]
        )
        
        return error_id
    
    def search_known_errors(self, error_message: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for known errors similar to the given error message.
        
        Args:
            error_message: Error message to search for
            limit: Maximum number of results to return
            
        Returns:
            List of known error dictionaries
        """
        self.logger.info(f"Searching for known errors similar to: {error_message}")
        
        # Search in vector database
        results = self.errors_collection.query(
            query_texts=[error_message],
            n_results=limit
        )
        
        # Get full error details from relational database
        errors = []
        if results and results['ids'] and results['ids'][0]:
            cursor = self.db_conn.cursor()
            for error_id in results['ids'][0]:
                cursor.execute("SELECT * FROM known_errors WHERE id = ?", (error_id,))
                error_row = cursor.fetchone()
                
                if error_row:
                    errors.append(dict(error_row))
        
        return errors
    
    def add_server_config(self, config: Dict[str, Any]) -> str:
        """
        Add a server configuration to the knowledge base.
        
        Args:
            config: Configuration dictionary with server_id, config_type, name, and content
            
        Returns:
            Configuration ID
        """
        config_id = str(uuid.uuid4())
        now = self._get_timestamp()
        
        self.logger.info(f"Adding server configuration to knowledge base: {config['name']}")
        
        # Add to relational database
        cursor = self.db_conn.cursor()
        cursor.execute(
            '''
            INSERT INTO server_configs
            (id, server_id, config_type, name, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                config_id,
                config['server_id'],
                config['config_type'],
                config['name'],
                config['content'],
                now,
                now
            )
        )
        
        self.db_conn.commit()
        
        # Add to vector database for semantic search
        config_text = f"""
        Server ID: {config['server_id']}
        Configuration Type: {config['config_type']}
        Name: {config['name']}
        
        Content:
        {config['content']}
        """
        
        metadata = {
            'id': config_id,
            'server_id': config['server_id'],
            'config_type': config['config_type'],
            'name': config['name'],
            'created_at': now
        }
        
        self.configs_collection.add(
            ids=[config_id],
            documents=[config_text.strip()],
            metadatas=[metadata]
        )
        
        return config_id
    
    def add_server(self, server: Dict[str, Any]) -> str:
        """
        Add a server to the knowledge base.
        
        Args:
            server: Server dictionary with hostname, ip_address, etc.
            
        Returns:
            Server ID
        """
        server_id = server.get('id', str(uuid.uuid4()))
        now = self._get_timestamp()
        
        self.logger.info(f"Adding server to knowledge base: {server['hostname']}")
        
        # Add to relational database
        cursor = self.db_conn.cursor()
        cursor.execute(
            '''
            INSERT INTO servers
            (id, hostname, ip_address, os_type, os_version, role, status, last_check, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                server_id,
                server['hostname'],
                server.get('ip_address', ''),
                server.get('os_type', ''),
                server.get('os_version', ''),
                server.get('role', ''),
                server.get('status', 'unknown'),
                now,
                json.dumps(server.get('metadata', {}))
            )
        )
        
        self.db_conn.commit()
        
        return server_id
    
    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a server from the knowledge base.
        
        Args:
            server_id: ID of the server
            
        Returns:
            Server dictionary or None if not found
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        server = dict(result)
        server['metadata'] = json.loads(server['metadata']) if server['metadata'] else {}
        
        return server
    
    def _format_steps_for_embedding(self, steps: List[Dict[str, Any]]) -> str:
        """Format task steps for embedding in the vector database."""
        steps_text = ""
        for i, step in enumerate(steps):
            result_text = json.dumps(step.get('result')) if step.get('result') else 'None'
            steps_text += f"Step {i+1}: {step['description']} - Status: {step['status']} - Result: {result_text}\n"
        return steps_text
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp string."""
        return datetime.now().isoformat()
    
    def close(self) -> None:
        """Close database connections."""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
        self.logger.info("Knowledge Base connections closed") 