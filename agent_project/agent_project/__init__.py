"""
Agent Project - A package for building AutoGen agents with team capabilities
"""

__version__ = "0.1.0"

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is not installed, display a message when imported directly
    import sys
    if __name__ != "__main__":
        print("Warning: python-dotenv is not installed. Environment variables won't be loaded from .env files.")
        print("To enable this feature, install with: pip install python-dotenv")

# Provide convenience imports
from agent_project.models.clients import create_model_client
from agent_project.agents import (
    python_dev_agent,
    code_reviewer_agent,
    product_owner_agent,
    qa_engineer_agent,
    scrum_master_agent
)
from agent_project.agents.dev_agents import (
    use_python_dev_agent,
    use_python_dev_agent_streaming,
    use_code_reviewer_agent,
    agile_development_workflow,
    develop_and_review,
    execute_code,
    install_package
)
from agent_project.teams import ScrumTeam, use_scrum_team

__all__ = [
    "create_model_client",
    "python_dev_agent",
    "code_reviewer_agent", 
    "product_owner_agent",
    "qa_engineer_agent",
    "scrum_master_agent",
    "ScrumTeam",
    "use_scrum_team",
    "use_python_dev_agent",
    "use_python_dev_agent_streaming",
    "use_code_reviewer_agent",
    "agile_development_workflow",
    "develop_and_review",
    "execute_code",
    "install_package"
] 