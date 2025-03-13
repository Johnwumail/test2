#!/usr/bin/env python3
"""
Setup script for IT Admin Agent.

This script installs the IT Admin Agent as a package.
"""
from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Read long description from README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="itadmin-agent",
    version="0.1.0",
    description="IT Admin Agent for Datacenter Management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="IT Admin Agent Team",
    author_email="example@example.com",
    url="https://github.com/example/itadmin-agent",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "itadmin=entry_points:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Systems Administration",
    ],
) 