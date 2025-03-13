"""
Entry points module for CLI installation.

These functions act as entry points for CLI commands when the package is installed.
"""
from cli import main as cli_main


def cli():
    """Entry point for the 'itadmin' command."""
    cli_main() 