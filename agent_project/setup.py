from setuptools import setup, find_packages

setup(
    name="agent-project",
    version="0.1.0",
    description="A package for building AutoGen agents",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/agent-project",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "autogen-core>=0.4.0",
        "autogen-ext[openai]>=0.4.0",
        "autogen-agentchat>=0.4.0",
        "autogen-ext[local-code-execution]>=0.4.0",
    ],
) 