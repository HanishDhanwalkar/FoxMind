# FoxMind
A LLM-powered browser automation agent using Ollama + Selenium + Firefox.

A scalable Python framework for browser automation powered by **LLaMA 3.2** running locally via **Ollama** and **Selenium WebDriver**. The agent interprets natural language instructions and autonomously controls Firefox to complete web-based tasks, requesting human assistance only when necessary.

## 🚀 Features

- **Local LLM Integration**: Uses Ollama to run LLaMA 3.2 locally for privacy and control
- **Intelligent Browser Control**: Selenium-based Firefox automation with smart element detection
- **Human-in-the-Loop**: Automatically requests help for CAPTCHAs, 2FA, and ambiguous situations
- **Scalable Architecture**: Modular design with clear separation of concerns
- **Error Recovery**: Built-in retry logic and fallback strategies
- **Configuration Management**: Flexible configuration via environment variables or JSON
- **Comprehensive Logging**: Detailed logging and screenshot capture for debugging

## 📋 Prerequisites

- Python 3.8+
- Firefox browser installed
- Ollama installed and running
- geckodriver in PATH

## ⚡ Quick Start

### 1. Install Ollama and LLaMA 3.2

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull LLaMA 3.2 model
ollama pull llama3.2

# Start Ollama service
ollama serve
```

### 2. Install Dependencies

```bash
# Clone and setup
git clone <repository-url>
cd llm-browser-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install geckodriver (macOS)
brew install geckodriver

# Or download manually from: https://github.com/mozilla/geckodriver/releases
```

### 3. Run Your First Task

```bash
# Simple CLI usage
python -m agents.cli "Search for 'Python automation' on Google and click the first result" --url https://google.com

# With custom options
python -m agents.cli "Fill out contact form with test data" --url https://example.com/contact --headless --max-steps 20
```

### 4. Programmatic Usage

```python
import asyncio
from agents import BrowserAgent

async def main():
    agent = BrowserAgent(headless=False)
    
    result = await agent.execute_task(
        objective="Search for 'browser automation' and bookmark the first result",
        starting_url="https://google.com"
    )
    
    print(f"Task completed: {result}")

asyncio.run(main())
```

## 🏗️ Architecture

```
agents/
├── browser_agent.py          # Main orchestration class
├── llm/
│   ├── ollama_client.py      # Ollama API integration
│   └── __init__.py
├── browser/
│   ├── selenium_controller.py # Firefox automation
│   └── __init__.py
├── utils/
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging utilities
│   ├── exceptions.py        # Custom exceptions
│   └── __init__.py
└── cli.py                   # Command-line interface
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=60

# Browser Configuration