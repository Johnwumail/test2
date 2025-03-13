#!/usr/bin/env python3
"""
Database Migration Utility

This module manages database schema migrations for the IT Admin Agent system.
It helps apply schema changes while preserving existing data.
"""
import os
import sys
import argparse
import logging
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from utils.config_loader import ConfigLoader
from utils.logging_setup import setup_logging


class Migration:
    """Class representing a database migration."""
    
    def __init__(self, version, description, up_sql, down_sql=None):
        """
        Initialize a migration.
        
        Args:
            version: Migration version
            description: Migration description
            up_sql: SQL statements to upgrade
            down_sql: SQL statements to downgrade (optional)
        """
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.id = self._generate_id()
    
    def _generate_id(self):
        """Generate a unique ID for the migration."""
        # Create a string combining version and description
        combined = f"{self.version}_{self.description}"
        # Generate MD5 hash
        return hashlib.md5(combined.encode()).hexdigest()


class MigrationManager:
    """Class for managing database migrations."""
    
    def __init__(self, db_path):
        """
        Initialize the migration manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Initialize migrations table if it doesn't exist
        self._initialize_migrations_table()
    
    def _connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def _disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def _initialize_migrations_table(self):
        """Initialize the migrations table if it doesn't exist."""
        try:
            self._connect()
            
            # Create migrations table if it doesn't exist
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            ''')
            
            self.conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error initializing migrations table: {str(e)}", exc_info=True)
            raise
            
        finally:
            self._disconnect()
    
    def get_applied_migrations(self):
        """
        Get a list of applied migrations.
        
        Returns:
            List of migration IDs that have been applied
        """
        try:
            self._connect()
            
            self.cursor.execute("SELECT id FROM migrations ORDER BY applied_at")
            return [row[0] for row in self.cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Error getting applied migrations: {str(e)}", exc_info=True)
            return []
            
        finally:
            self._disconnect()
    
    def apply_migration(self, migration):
        """
        Apply a migration.
        
        Args:
            migration: Migration to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._connect()
            
            # Check if migration has already been applied
            self.cursor.execute("SELECT 1 FROM migrations WHERE id = ?", (migration.id,))
            if self.cursor.fetchone():
                self.logger.info(f"Migration {migration.version} already applied: {migration.description}")
                return True
            
            # Apply the migration
            self.logger.info(f"Applying migration {migration.version}: {migration.description}")
            
            # Split up_sql into individual statements
            statements = [stmt.strip() for stmt in migration.up_sql.split(';') if stmt.strip()]
            
            # Execute each statement
            for stmt in statements:
                self.cursor.execute(stmt)
            
            # Record the migration
            self.cursor.execute(
                "INSERT INTO migrations (id, version, description, applied_at) VALUES (?, ?, ?, ?)",
                (migration.id, migration.version, migration.description, datetime.now().isoformat())
            )
            
            self.conn.commit()
            self.logger.info(f"Migration {migration.version} applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying migration {migration.version}: {str(e)}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            return False
            
        finally:
            self._disconnect()
    
    def rollback_migration(self, migration):
        """
        Rollback a migration.
        
        Args:
            migration: Migration to rollback
            
        Returns:
            True if successful, False otherwise
        """
        if not migration.down_sql:
            self.logger.error(f"Cannot rollback migration {migration.version}: No down SQL provided")
            return False
        
        try:
            self._connect()
            
            # Check if migration has been applied
            self.cursor.execute("SELECT 1 FROM migrations WHERE id = ?", (migration.id,))
            if not self.cursor.fetchone():
                self.logger.info(f"Migration {migration.version} not applied: {migration.description}")
                return True
            
            # Apply the rollback
            self.logger.info(f"Rolling back migration {migration.version}: {migration.description}")
            
            # Split down_sql into individual statements
            statements = [stmt.strip() for stmt in migration.down_sql.split(';') if stmt.strip()]
            
            # Execute each statement
            for stmt in statements:
                self.cursor.execute(stmt)
            
            # Remove the migration record
            self.cursor.execute("DELETE FROM migrations WHERE id = ?", (migration.id,))
            
            self.conn.commit()
            self.logger.info(f"Migration {migration.version} rolled back successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rolling back migration {migration.version}: {str(e)}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            return False
            
        finally:
            self._disconnect()


def load_migrations(migrations_dir):
    """
    Load migrations from migration files.
    
    Args:
        migrations_dir: Directory containing migration files
        
    Returns:
        List of Migration objects
    """
    logger = logging.getLogger(__name__)
    migrations = []
    
    # Create migrations directory if it doesn't exist
    os.makedirs(migrations_dir, exist_ok=True)
    
    # Get all .json files in the migrations directory
    migration_files = sorted(Path(migrations_dir).glob("*.json"))
    
    for file_path in migration_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Create migration object
                migration = Migration(
                    version=data.get('version'),
                    description=data.get('description'),
                    up_sql=data.get('up_sql'),
                    down_sql=data.get('down_sql')
                )
                
                migrations.append(migration)
                logger.debug(f"Loaded migration {migration.version}: {migration.description}")
                
        except Exception as e:
            logger.error(f"Error loading migration from {file_path}: {str(e)}", exc_info=True)
    
    return migrations


def create_migration(migrations_dir, description, up_sql, down_sql=None):
    """
    Create a new migration file.
    
    Args:
        migrations_dir: Directory to store migration files
        description: Migration description
        up_sql: SQL statements to upgrade
        down_sql: SQL statements to downgrade (optional)
        
    Returns:
        Path to created migration file
    """
    logger = logging.getLogger(__name__)
    
    # Create migrations directory if it doesn't exist
    os.makedirs(migrations_dir, exist_ok=True)
    
    # Generate version based on timestamp
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create migration data
    migration_data = {
        "version": version,
        "description": description,
        "up_sql": up_sql,
        "down_sql": down_sql
    }
    
    # Create filename
    filename = f"{version}_{description.lower().replace(' ', '_')}.json"
    file_path = Path(migrations_dir) / filename
    
    # Write migration file
    with open(file_path, 'w') as f:
        json.dump(migration_data, f, indent=2)
    
    logger.info(f"Created migration file: {file_path}")
    return file_path


def migrate(config_path, target_version=None):
    """
    Apply pending migrations.
    
    Args:
        config_path: Path to configuration file
        target_version: Target migration version (optional)
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting database migration")
    
    try:
        # Load configuration
        config = ConfigLoader.load(Path(config_path))
        
        # Get database path
        db_config = config['knowledge_base']['relational_db']
        db_path = Path(db_config['path'])
        
        # Check if database exists
        if not db_path.exists():
            logger.error(f"Database not found at {db_path}. Run db_init.py first.")
            return False
        
        # Get migrations directory
        migrations_dir = Path(parent_dir) / "migrations"
        
        # Load migrations
        migrations = load_migrations(migrations_dir)
        if not migrations:
            logger.info("No migrations found")
            return True
        
        # Sort migrations by version
        migrations.sort(key=lambda m: m.version)
        
        # Initialize migration manager
        manager = MigrationManager(db_path)
        
        # Get applied migrations
        applied_migrations = manager.get_applied_migrations()
        
        # Apply pending migrations
        for migration in migrations:
            # Stop if we've reached the target version
            if target_version and migration.version > target_version:
                break
                
            # Skip if already applied
            if migration.id in applied_migrations:
                continue
                
            # Apply migration
            if not manager.apply_migration(migration):
                return False
        
        logger.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}", exc_info=True)
        return False


def rollback(config_path, steps=1):
    """
    Rollback migrations.
    
    Args:
        config_path: Path to configuration file
        steps: Number of migrations to roll back
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting database rollback ({steps} steps)")
    
    try:
        # Load configuration
        config = ConfigLoader.load(Path(config_path))
        
        # Get database path
        db_config = config['knowledge_base']['relational_db']
        db_path = Path(db_config['path'])
        
        # Check if database exists
        if not db_path.exists():
            logger.error(f"Database not found at {db_path}. Run db_init.py first.")
            return False
        
        # Get migrations directory
        migrations_dir = Path(parent_dir) / "migrations"
        
        # Load migrations
        migrations = load_migrations(migrations_dir)
        if not migrations:
            logger.info("No migrations found")
            return True
        
        # Sort migrations by version in reverse order
        migrations.sort(key=lambda m: m.version, reverse=True)
        
        # Initialize migration manager
        manager = MigrationManager(db_path)
        
        # Get applied migrations
        applied_migrations = manager.get_applied_migrations()
        
        # Count rollbacks performed
        rollbacks_performed = 0
        
        # Rollback the specified number of migrations
        for migration in migrations:
            # Skip if not applied
            if migration.id not in applied_migrations:
                continue
                
            # Rollback migration
            if not manager.rollback_migration(migration):
                return False
                
            rollbacks_performed += 1
            
            # Stop if we've rolled back enough migrations
            if rollbacks_performed >= steps:
                break
        
        logger.info(f"Database rollback completed successfully ({rollbacks_performed} steps)")
        return True
        
    except Exception as e:
        logger.error(f"Error during database rollback: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Manage IT Admin Agent database migrations")
    parser.add_argument(
        "--config", 
        type=str, 
        default="../config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Apply migrations")
    migrate_parser.add_argument(
        "--target", 
        type=str, 
        help="Target migration version"
    )
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migrations")
    rollback_parser.add_argument(
        "--steps", 
        type=int, 
        default=1,
        help="Number of migrations to roll back"
    )
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument(
        "description", 
        type=str, 
        help="Migration description"
    )
    create_parser.add_argument(
        "--up", 
        type=str, 
        help="Path to file containing SQL statements for upgrading"
    )
    create_parser.add_argument(
        "--down", 
        type=str, 
        help="Path to file containing SQL statements for downgrading"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_dir = Path(parent_dir) / "logs"
    os.makedirs(log_dir, exist_ok=True)
    setup_logging(args.log_level, log_dir)
    
    # Run the specified command
    if args.command == "migrate":
        success = migrate(args.config, args.target)
    elif args.command == "rollback":
        success = rollback(args.config, args.steps)
    elif args.command == "create":
        migrations_dir = Path(parent_dir) / "migrations"
        
        # Read SQL files
        up_sql = ""
        down_sql = None
        
        if args.up:
            with open(args.up, 'r') as f:
                up_sql = f.read()
        else:
            up_sql = input("Enter SQL statements for upgrading (end with empty line):\n")
        
        if args.down:
            with open(args.down, 'r') as f:
                down_sql = f.read()
        else:
            down_input = input("Enter SQL statements for downgrading (optional, end with empty line):\n")
            if down_input:
                down_sql = down_input
        
        # Create migration
        file_path = create_migration(migrations_dir, args.description, up_sql, down_sql)
        print(f"Created migration file: {file_path}")
        success = True
    else:
        parser.print_help()
        return 1
    
    if success:
        print(f"Command '{args.command}' completed successfully.")
        return 0
    else:
        print(f"Command '{args.command}' failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 