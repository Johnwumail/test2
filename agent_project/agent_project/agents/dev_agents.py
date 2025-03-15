"""
Agent definitions for the development team.
"""

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from autogen_core.code_executor import CodeBlock
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from pathlib import Path
import sys
import asyncio
import venv

from agent_project.models.clients import gemini_model_client

# If on Windows, use WindowsProactorEventLoopPolicy to avoid issues with subprocesses
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Create a work directory for code execution
work_dir = Path("./code_execution_workspace")
work_dir.mkdir(exist_ok=True)

# Set up a virtual environment for code execution
venv_dir = work_dir / ".venv"
venv_builder = venv.EnvBuilder(with_pip=True)

# Create the virtual environment if it doesn't exist
if not venv_dir.exists():
    print(f"Creating virtual environment in {venv_dir}...")
    venv_builder.create(venv_dir)

# Get the virtual environment context
venv_context = venv_builder.ensure_directories(venv_dir)

# Create the LocalCommandLineCodeExecutor with the virtual environment
code_executor = LocalCommandLineCodeExecutor(
    timeout=60,  # 60 seconds timeout for code execution
    work_dir=work_dir,
    virtual_env_context=venv_context,  # Use the virtual environment for code execution
)


# Function to install packages in the virtual environment
async def install_package(package_name: str) -> str:
    """Install a Python package in the virtual environment."""
    try:
        # Create a code block to install the package using pip
        code_block = CodeBlock(
            language="bash",
            code=f"pip install {package_name}"
        )
        
        # Execute the code block
        result = await code_executor.execute_code_blocks(
            [code_block],
            cancellation_token=CancellationToken(),
        )
        
        return f"Package installation result:\n{result.output}"
    except Exception as e:
        return f"Error installing package: {str(e)}"


# Function to execute Python code using the LocalCommandLineCodeExecutor
async def execute_code(code: str, language: str = "python") -> str:
    """Execute code using the LocalCommandLineCodeExecutor and return the result."""
    try:
        # Create a code block
        code_block = CodeBlock(language=language, code=code)
        
        # Execute the code
        result = await code_executor.execute_code_blocks(
            [code_block],
            cancellation_token=CancellationToken(),
        )
        
        # Return the execution result
        return f"Code execution result:\n{result.output}"
    except Exception as e:
        return f"Error executing code: {str(e)}"


# Create the Python developer agent
python_dev_agent = AssistantAgent(
    name="python_developer",
    model_client=gemini_model_client,
    system_message="""You are an expert Python code developer. 
You excel at writing clean, efficient, and well-documented Python code.
Always follow PEP 8 style guidelines and best practices.
When asked to write code, include detailed comments and explanations.
You can execute code to test solutions.

To execute code, you can use the execute_code tool. The code will be executed in a secure environment.
If your code requires external packages, you can install them using the install_package tool.
""",
    tools=[execute_code, install_package],
)


# Create the code reviewer agent
code_reviewer_agent = AssistantAgent(
    name="code_reviewer",
    model_client=gemini_model_client,
    system_message="""You are an expert Python code reviewer.
Your job is to review Python code for:
1. Bugs and logical errors
2. Security vulnerabilities
3. Performance issues
4. Style and PEP 8 compliance
5. Readability and maintainability
6. Documentation quality

Provide specific, actionable feedback with examples of how to improve the code.
Be thorough but constructive in your critique.
When appropriate, suggest alternative implementations that improve the code.
You can execute code to verify its correctness.
If code is good, say Approved.

To execute code, you can use the execute_code tool. The code will be executed in a secure environment.
If you need to install packages to test the code, you can use the install_package tool.
""",
    tools=[execute_code, install_package],
)


# Create a Product Owner agent
product_owner_agent = AssistantAgent(
    name="product_owner",
    description="Product Owner who defines requirements and prioritizes features",
    model_client=gemini_model_client,
    system_message="""You are the Product Owner for this development team.
Your responsibilities include:
1. Clearly defining project requirements and acceptance criteria
2. Answering questions about feature priorities and business value
3. Providing clarification on user stories and use cases
4. Making final decisions about product features
5. Validating if implementations meet the business requirements

You should ensure all requirements are SMART: Specific, Measurable, Achievable, Relevant, and Time-bound.
You can terminate the conversation by saying "TERMINATE" when you are satisfied with the solution.
""",
)


# Create a QA Engineer agent
qa_engineer_agent = AssistantAgent(
    name="qa_engineer",
    description="QA Engineer who tests code and identifies potential issues",
    model_client=gemini_model_client,
    system_message="""You are the QA Engineer for this development team.
Your responsibilities include:
1. Suggesting test cases for the code being developed
2. Identifying edge cases and potential bugs
3. Reviewing code from a testing perspective
4. Ensuring code meets quality standards
5. Validating that error handling is appropriate

You can execute code to verify functionality.
""",
    tools=[execute_code],
)


# Create the Scrum Master agent as an AssistantAgent (fully automated)
scrum_master_agent = AssistantAgent(
    name="scrum_master",
    description="Scrum Master who facilitates the development process and provides guidance",
    model_client=gemini_model_client,
    system_message="""You are the Scrum Master for this development team.
Your responsibilities include:
1. Facilitating the development process and ensuring smooth team collaboration
2. Providing guidance on best practices and software development principles
3. Reviewing code and requirements to ensure alignment with project goals
4. Making final approval decisions on code and features
5. Identifying and removing obstacles in the development process

As a Scrum Master, you should:
- Be constructive in your feedback
- Help the development team adhere to good coding practices
- Make clear approval decisions (type "APPROVE" when satisfied with a solution)
- Ask clarifying questions when requirements or implementations are unclear
- Suggest improvements while respecting the expertise of team members

You have the authority to approve or request changes to code and features.
""",
)


# Example function to demonstrate using the developer agent
async def use_python_dev_agent(task: str):
    """Function to run the Python developer agent with a given task."""
    response = await python_dev_agent.on_messages(
        [TextMessage(content=task, source="user")],
        cancellation_token=CancellationToken(),
    )
    return response


# Example function to demonstrate using the developer agent with streaming
async def use_python_dev_agent_streaming(task: str):
    """Function to run the Python developer agent with streaming."""
    await Console(
        python_dev_agent.on_messages_stream(
            [TextMessage(content=task, source="user")],
            cancellation_token=CancellationToken(),
        ),
        output_stats=True,  # Enable stats printing
    )


# Example function to demonstrate using the code reviewer agent
async def use_code_reviewer_agent(code: str):
    """Function to run the code reviewer agent to review provided code."""
    prompt = f"Please review the following Python code and provide feedback:\n\n```python\n{code}\n```"
    response = await code_reviewer_agent.on_messages(
        [TextMessage(content=prompt, source="user")],
        cancellation_token=CancellationToken(),
    )
    return response


# Function for a new agile development workflow with AI Scrum Master
async def agile_development_workflow(task: str):
    """Function that demonstrates a complete agile development workflow with an AI Scrum Master."""
    # Setup termination condition
    termination = TextMentionTermination("APPROVE")
    
    # Setup the team with the AI scrum master
    team = RoundRobinGroupChat(
        [python_dev_agent, code_reviewer_agent, scrum_master_agent],
        termination_condition=termination
    )
    
    # Run the team with the task
    print("🏃‍♂️ Starting Agile Development Workflow")
    print(f"📋 Task: {task}")
    print("\n💬 Team discussion will start now. The AI Scrum Master will coordinate the process and approve solutions.")
    
    # Start the team run with streaming to console
    await Console(
        team.run_stream(task=task),
        output_stats=True
    )
    
    print("\n✅ Development workflow completed! The solution has been approved.")


# Example function to demonstrate a development and review workflow
async def develop_and_review(task: str):
    """Function that demonstrates a complete development and review workflow."""
    print("🚀 STEP 1: Developer creates code based on requirements")
    dev_response = await python_dev_agent.on_messages(
        [TextMessage(content=task, source="user")],
        cancellation_token=CancellationToken(),
    )
    
    # Extract code from the developer's response
    dev_message = dev_response.chat_message.content
    print("\n----- DEVELOPER'S SOLUTION -----\n")
    print(dev_message)
    
    # Find code blocks in the developer's response
    import re
    code_blocks = re.findall(r'```python\n(.*?)\n```', dev_message, re.DOTALL)
    
    if not code_blocks:
        print("\n❌ No code found in developer's response")
        return
    
    # Send the first code block to the reviewer
    code_to_review = code_blocks[0]
    print("\n\n🔍 STEP 2: Code reviewer analyzes the solution")
    
    review_prompt = f"Review this Python code:\n\n```python\n{code_to_review}\n```"
    await Console(
        code_reviewer_agent.on_messages_stream(
            [TextMessage(content=review_prompt, source="user")],
            cancellation_token=CancellationToken(),
        ),
        output_stats=True,
    )
    
    # Ask the AI scrum master for final approval
    print("\n\n👨‍💼 STEP 3: Scrum Master provides final approval")
    scrum_prompt = f"Please review the code and provide your final assessment. Type 'APPROVE' if you're satisfied or provide feedback for improvements:\n\n```python\n{code_to_review}\n```"
    
    scrum_response = await scrum_master_agent.on_messages(
        [TextMessage(content=scrum_prompt, source="user")],
        cancellation_token=CancellationToken(),
    )
    print(f"\nScrum Master response: {scrum_response.chat_message.content}")


# Example function to demonstrate running a shell script
async def execute_shell_script(script: str):
    """Run a shell script using the LocalCommandLineCodeExecutor."""
    result = await execute_code(script, language="bash")
    print(result)


# Example function to demonstrate the virtual environment setup
async def setup_development_environment(required_packages: list):
    """Set up the development environment by installing required packages."""
    print(f"Setting up development environment with packages: {', '.join(required_packages)}")
    for package in required_packages:
        print(f"Installing {package}...")
        result = await install_package(package)
        print(result)
    print("Development environment setup complete!") 