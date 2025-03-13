#!/usr/bin/env python3
"""
IT Admin Agent System - Main Application Entry Point

This module initializes and starts the IT Admin Agent system.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from agent.orchestrator import AgentOrchestrator
from utils.config_loader import ConfigLoader
from utils.logging_setup import setup_logging
from ui.dashboard import start_dashboard
from api.server import start_api_server


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="IT Admin Agent System")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["api", "dashboard", "full", "agent-only"],
        default="full",
        help="Execution mode"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from config"
    )
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Load configuration
    config_path = Path(__file__).parent / args.config
    try:
        config = ConfigLoader.load(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Set up logging
    log_level = args.log_level or config["system"]["log_level"]
    log_dir = Path(__file__).parent / config["monitoring"]["logging"]["file_path"]
    os.makedirs(log_dir, exist_ok=True)
    setup_logging(log_level, log_dir)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting IT Admin Agent System v{config['system']['version']}")
    logger.info(f"Environment: {config['system']['environment']}")
    logger.info(f"Mode: {args.mode}")
    
    # Initialize the agent orchestrator
    try:
        orchestrator = AgentOrchestrator(config)
        logger.info("Agent Orchestrator initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize Agent Orchestrator: {e}")
        sys.exit(1)
    
    # Start components based on mode
    if args.mode in ["full", "agent-only"]:
        try:
            orchestrator.start()
            logger.info("Agent Orchestrator started successfully")
        except Exception as e:
            logger.critical(f"Failed to start Agent Orchestrator: {e}")
            sys.exit(1)
    
    if args.mode in ["full", "api"]:
        try:
            start_api_server(config, orchestrator)
            logger.info("API server started successfully")
        except Exception as e:
            logger.critical(f"Failed to start API server: {e}")
            if args.mode == "api":
                sys.exit(1)
    
    if args.mode in ["full", "dashboard"]:
        try:
            start_dashboard(config, orchestrator)
            logger.info("Dashboard started successfully")
        except Exception as e:
            logger.critical(f"Failed to start Dashboard: {e}")
            if args.mode == "dashboard":
                sys.exit(1)
    
    logger.info("IT Admin Agent System is running")
    
    # Keep the main thread running
    if args.mode != "dashboard":  # Dashboard has its own event loop
        try:
            # Wait indefinitely (until Ctrl+C)
            import time
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            # Graceful shutdown
            logger.info("Shutting down IT Admin Agent System")
            if args.mode in ["full", "agent-only"]:
                orchestrator.stop()
            logger.info("Shutdown complete")


if __name__ == "__main__":
    main() 