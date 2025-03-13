#!/usr/bin/env python3
"""
Test Runner for IT Admin Agent

This script runs tests for the IT Admin Agent system.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for IT Admin Agent")
    parser.add_argument(
        "--unit", action="store_true", help="Run only unit tests"
    )
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--test-path", type=str, help="Specific test path to run"
    )
    return parser.parse_args()


def run_tests(args):
    """Run tests with pytest."""
    # Set up the command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity if requested
    if args.verbose:
        cmd.append("-v")
    
    # Add markers based on args
    if args.unit and not args.integration:
        cmd.append("-m")
        cmd.append("unit")
    elif args.integration and not args.unit:
        cmd.append("-m")
        cmd.append("integration")
    
    # Add coverage if requested
    if args.coverage:
        cmd.append("--cov=itadmin_agent")
        cmd.append("--cov-report=term")
        cmd.append("--cov-report=html")
    
    # Add specific test path if provided
    if args.test_path:
        cmd.append(args.test_path)
    
    # Run the command
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    # Make sure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Run tests
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main()) 