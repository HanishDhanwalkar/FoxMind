#!/bin/bash
# Setup script for the browser agent

echo "Setting up LLM Browser Agent..."

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install geckodriver for Firefox
echo "Installing geckodriver..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    wget -O geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.33.0-linux64.tar.gz
    tar -xzf geckodriver.tar.gz
    sudo mv geckodriver /usr/local/bin/
    rm geckodriver.tar.gz
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install geckodriver
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "Please download geckodriver from https://github.com/mozilla/geckodriver/releases and add it to PATH"
fi

# Create directories
mkdir -p screenshots
mkdir -p logs

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Please install Ollama from https://ollama.ai"
    echo "After installation, run: ollama pull llama3.2"
else
    echo "Pulling LLaMA 3.2 model..."
    ollama pull llama3.2
fi

echo "Setup complete!"
echo "Usage: python -m agents.cli 'Your task objective here' --url https://example.com"
