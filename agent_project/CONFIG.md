# Configuration Guide for Agent Project

## API Keys Configuration

This project uses API keys for interacting with various language models. To keep these keys secure:

1. **DO NOT commit API keys to version control**
2. **Use environment variables instead**

## Setting Up Environment Variables

### For Linux/Mac:

Add the following to your `~/.bashrc`, `~/.zshrc`, or equivalent:

```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
export DEEPSEEK_API_KEY="your_deepseek_api_key_here"
# Add any other API keys as needed
```

Then apply the changes:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### For Windows:

Using Command Prompt as Administrator:
```cmd
setx GEMINI_API_KEY "your_gemini_api_key_here"
setx DEEPSEEK_API_KEY "your_deepseek_api_key_here"
```

## Using a .env File (Alternative)

You can also use a `.env` file in your project root:

1. Create a file named `.env` in your project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

2. Install python-dotenv:
```bash
pip install python-dotenv
```

3. Add this to the top of your main script:
```python
from dotenv import load_dotenv
load_dotenv()
```

4. Add `.env` to your `.gitignore` file:
```
# Add this to .gitignore
.env
```

## API Keys Used in This Project

1. **GEMINI_API_KEY**: Required for using Google's Gemini models
2. **DEEPSEEK_API_KEY**: Required for using DeepSeek language models

## Default Values

If no environment variables are set, the code will use placeholder values (`your_api_key_here`), which will not work for actual API calls. Make sure to set your actual API keys before running the application. 