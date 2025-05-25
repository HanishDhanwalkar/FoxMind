# examples/basic_usage.py
"""Basic usage examples for the browser agent."""

import asyncio
from agents import BrowserAgent

async def example_google_search():
    """Example: Search Google and click on first result."""
    agent = BrowserAgent(headless=False)
    
    result = await agent.execute_task(
        objective="Search for 'Python automation' on Google and click the first result",
        starting_url="https://google.com"
    )
    
    print(f"Task result: {result}")

async def example_form_filling():
    """Example: Fill out a contact form."""
    agent = BrowserAgent(headless=False)
    
    result = await agent.execute_task(
        objective="Fill out the contact form with name 'John Doe', email 'john@example.com', and message 'Hello from automation'",
        starting_url="https://example.com/contact"
    )
    
    print(f"Task result: {result}")

async def example_ecommerce_search():
    """Example: Search for products on an e-commerce site."""
    agent = BrowserAgent(headless=False)
    
    result = await agent.execute_task(
        objective="Search for 'wireless headphones' and add the first result to cart",
        starting_url="https://amazon.com"
    )
    
    print(f"Task result: {result}")

async def example_information_gathering():
    """Example: Gather information from a website."""
    agent = BrowserAgent(headless=False)
    
    result = await agent.execute_task(
        objective="Go to the company's about page and take a screenshot of the team section",
        starting_url="https://company.com"
    )
    
    print(f"Task result: {result}")

if __name__ == "__main__":
    # Run examples
    asyncio.run(example_google_search())
