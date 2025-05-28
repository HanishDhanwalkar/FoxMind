# agents/cli.py
"""Command-line interface for the browser agent."""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from .browser_agent import BrowserAgent
from .utils.config import Config
from .utils.logger import get_logger

logger = get_logger(__name__)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="LLM-powered browser automation agent"
    )
    
    parser.add_argument(
        "objective",
        help="The task objective to accomplish"
    )
    
    parser.add_argument(
        "--url",
        help="Starting URL for the task"
    )
    
    parser.add_argument(
        "--model",
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="Maximum number of steps to attempt (default: 50)"
    )
    
    parser.add_argument(
        "--config",
        help="Path to JSON configuration file"
    )
    
    parser.add_argument(
        "--output",
        help="Path to save execution results as JSON"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

async def run_agent(args) -> Dict:
    """Run the browser agent with given arguments."""
    
    # Load configuration
    config = Config()
    if args.config:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            config = Config.from_dict(config_dict)
    
    # Override config with CLI arguments
    if args.model:
        config.ollama.model = args.model
    if args.headless:
        config.browser.headless = args.headless
    if args.max_steps:
        config.agent.max_steps = args.max_steps
    
    # Initialize agent
    agent = BrowserAgent(
        ollama_model=config.ollama.model,
        headless=config.browser.headless,
        max_steps=config.agent.max_steps
    )
    
    try:
        # Check if Ollama is running
        if not await agent.llm.is_healthy():
            logger.warning("Ollama service not accessible, attempting to pull model...")
            success = await agent.llm.pull_model()
            if not success:
                raise Exception("Failed to setup Ollama model")
        
        # Execute the task
        result = await agent.execute_task(
            objective=args.objective,
            starting_url=args.url
        )
        
        return result
        
    except KeyboardInterrupt:
        logger.info("Task interrupted by user")
        return {"success": False, "reason": "interrupted"}
    except Exception as e:
        logger.error(f"Task execution failed: {str(e)}")
        return {"success": False, "reason": "error", "message": str(e)}
    finally:
        agent.cleanup()

def main():
    """Main CLI entry point."""
    args = parse_arguments()
    
    # Set up logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Run the agent
        result = asyncio.run(run_agent(args))
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result.get("success", False) else 1)
        
    except Exception as e:
        logger.error(f"CLI execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
