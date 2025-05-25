
# scripts/run_examples.py
#!/usr/bin/env python3
"""Script to run example tasks."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.basic_usage import (
    example_google_search,
    example_form_filling,
    example_information_gathering
)
from examples.advanced_usage import (
    example_with_custom_config,
    example_multi_step_workflow
)

async def main():
    """Run example demonstrations."""
    print("🤖 LLM Browser Agent Examples")
    print("=" * 40)
    
    examples = [
        ("Google Search", example_google_search),
        ("Custom Config", example_with_custom_config),
        ("Information Gathering", example_information_gathering),
    ]
    
    for name, example_func in examples:
        print(f"\n📋 Running: {name}")
        print("-" * 30)
        
        try:
            await example_func()
            print(f"✅ {name} completed")
        except Exception as e:
            print(f"❌ {name} failed: {str(e)}")
        
        input("\nPress Enter to continue to next example...")

if __name__ == "__main__":
    asyncio.run(main())