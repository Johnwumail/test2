#!/usr/bin/env python3
"""
Environment Setup Script

This script helps you set up your environment variables for API keys.
It creates a .env file in the project root directory.
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create a .env file with the required API keys."""
    project_root = Path(__file__).parent
    env_path = project_root / ".env"
    
    # Check if .env file already exists
    if env_path.exists():
        overwrite = input(".env file already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Setup canceled. Your existing .env file was not modified.")
            return
    
    # Get API keys from user
    gemini_key = input("Enter your Gemini API key (or press Enter to skip): ")
    deepseek_key = input("Enter your DeepSeek API key (or press Enter to skip): ")
    
    # Create .env file content
    env_content = []
    if gemini_key:
        env_content.append(f"GEMINI_API_KEY={gemini_key}")
    else:
        env_content.append("# GEMINI_API_KEY=your_gemini_api_key_here")
    
    if deepseek_key:
        env_content.append(f"DEEPSEEK_API_KEY={deepseek_key}")
    else:
        env_content.append("# DEEPSEEK_API_KEY=your_deepseek_api_key_here")
    
    # Write to file
    with open(env_path, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f".env file created at {env_path}")
    print("\nTo use these environment variables in your current shell:")
    if sys.platform.startswith('win'):
        print("Run these commands:")
        if gemini_key:
            print(f'set GEMINI_API_KEY={gemini_key}')
        if deepseek_key:
            print(f'set DEEPSEEK_API_KEY={deepseek_key}')
    else:
        print("Run these commands:")
        if gemini_key:
            print(f'export GEMINI_API_KEY="{gemini_key}"')
        if deepseek_key:
            print(f'export DEEPSEEK_API_KEY="{deepseek_key}"')
    
    print("\nRemember to install python-dotenv to load these variables automatically:")
    print("pip install python-dotenv")


def main():
    """Main function to run the setup."""
    print("===== API Key Environment Setup =====")
    print("This script will create a .env file for your API keys.")
    print("These keys will be loaded as environment variables.")
    print("Note: .env files are excluded from git in the .gitignore file.")
    
    proceed = input("Proceed with setup? (y/n): ")
    if proceed.lower() == 'y':
        create_env_file()
    else:
        print("Setup canceled.")


if __name__ == "__main__":
    main() 