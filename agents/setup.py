# setup.py
from setuptools import setup, find_packages

setup(
    name="llm-browser-agent",
    version="0.1.0",
    description="LLM-powered browser automation agent using Ollama and Selenium",
    packages=find_packages(),
    install_requires=[
        "selenium>=4.15.2",
        "aiohttp>=3.9.1",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "browser-agent=agents.cli:main",
        ],
    },
)