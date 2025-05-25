
# examples/advanced_usage.py
"""Advanced usage examples with custom configurations."""

import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.browser_agent import BrowserAgent
from agents.utils.config import Config


async def example_with_custom_config():
    """Example using custom configuration."""
    
    # Custom configuration
    config_dict = {
        "ollama": {
            "model": "llama3.2",
            "timeout": 120
        },
        "browser": {
            "headless": False,
            "window_width": 1440,
            "window_height": 900
        },
        "agent": {
            "max_steps": 30,
            "max_errors": 5
        }
    }
    
    config = Config.from_dict(config_dict)
    
    agent = BrowserAgent(
        ollama_model=config.ollama.model,
        headless=config.browser.headless,
        max_steps=config.agent.max_steps
    )
    
    result = await agent.execute_task(
        objective="Navigate to Reddit, search for 'python automation', and bookmark the top post",
        starting_url="https://reddit.com"
    )
    
    print(f"Task result: {result}")

async def example_multi_step_workflow():
    """Example of a complex multi-step workflow."""
    agent = BrowserAgent(headless=False)
    
    tasks = [
        {
            "objective": "Go to GitHub and search for 'browser automation' repositories",
            "starting_url": "https://github.com"
        },
        {
            "objective": "Click on the first repository and star it",
            "starting_url": None  # Continue from current page
        },
        {
            "objective": "Navigate to the repository's README and take a screenshot",
            "starting_url": None
        }
    ]
    
    results = []
    for task in tasks:
        result = await agent.execute_task(
            objective=task["objective"],
            starting_url=task["starting_url"]
        )
        results.append(result)
        
        if not result.get("success", False):
            print(f"Task failed: {result}")
            break
    
    print(f"Workflow results: {json.dumps(results, indent=2)}")

async def example_error_handling():
    """Example demonstrating error handling and recovery."""
    agent = BrowserAgent(headless=False, max_steps=10)
    
    # Intentionally problematic task to test error handling
    result = await agent.execute_task(
        objective="Click on a button that doesn't exist and then search for something",
        starting_url="https://example.com"
    )
    
    print(f"Error handling result: {result}")

if __name__ == "__main__":
    asyncio.run(example_with_custom_config())
