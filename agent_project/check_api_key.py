#!/usr/bin/env python3
"""
API Key Checker Script

This script checks if your API keys are properly configured and validates them.
"""

import os
import sys
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv is installed")
    load_dotenv()
    print("✅ Loaded environment variables from .env file (if it exists)")
except ImportError:
    print("❌ python-dotenv is not installed")
    print("   Install it with: pip install python-dotenv")


def check_api_key(key_name, provider_name):
    """Check if an API key is set and report its status."""
    key_value = os.environ.get(key_name)
    
    if not key_value:
        print(f"❌ {key_name} is not set in environment variables")
        return False
    
    if key_value == "your_api_key_here":
        print(f"❌ {key_name} has the placeholder value 'your_api_key_here'")
        return False
    
    # Mask the API key for security
    masked_key = f"{key_value[:4]}...{key_value[-4:]}" if len(key_value) > 8 else "***"
    print(f"✅ {key_name} is set: {masked_key}")
    
    return True


def suggest_fix(key_name):
    """Suggest how to fix missing API keys."""
    print("\nTo fix this issue:")
    print(f"1. Get your {key_name} from the provider's website")
    if key_name == "GEMINI_API_KEY":
        print("   Visit: https://makersuite.google.com/app/apikey")
    print(f"2. Set up your {key_name} using one of these methods:")
    print("   a) Run the setup script: python setup_env.py")
    print("   b) Set it manually in your environment:")
    if sys.platform.startswith('win'):
        print(f"      set {key_name}=your_actual_key_here")
    else:
        print(f"      export {key_name}=\"your_actual_key_here\"")
    print("   c) Create a .env file in the project root with:")
    print(f"      {key_name}=your_actual_key_here")


def main():
    """Main function to check API keys."""
    print("===== API Key Configuration Check =====\n")
    
    # Check python-dotenv installation
    if 'dotenv' not in sys.modules:
        print("ℹ️ Recommendation: Install python-dotenv for easier configuration")
        print("   pip install python-dotenv")
    
    # Check Gemini API key
    gemini_ok = check_api_key("GEMINI_API_KEY", "Google")
    
    # Check DeepSeek API key
    deepseek_ok = check_api_key("DEEPSEEK_API_KEY", "DeepSeek")
    
    print("\n===== Check Summary =====")
    if gemini_ok:
        print("✅ Gemini API key is properly configured")
    else:
        print("❌ Gemini API key is not properly configured")
        suggest_fix("GEMINI_API_KEY")
    
    if deepseek_ok:
        print("✅ DeepSeek API key is properly configured")
    else:
        print("ℹ️ DeepSeek API key is not set (only needed if using DeepSeek models)")
    
    # Check environment setup for python-dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"✅ .env file exists at {env_path}")
    else:
        print(f"ℹ️ No .env file found at {env_path}")
        print("   You can create one by running: python setup_env.py")
    
    if not (gemini_ok or deepseek_ok):
        print("\n❌ No valid API keys configured. The application will not work without at least one valid API key.")
        print("   Please set up your API keys as suggested above.")
    else:
        print("\n✅ Configuration looks good! You can now run the application.")


if __name__ == "__main__":
    main() 