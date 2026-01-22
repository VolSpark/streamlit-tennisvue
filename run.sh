#!/bin/bash
# run.sh - Mac/Linux shell script to set up and run the Streamlit app
# Usage: bash run.sh

echo "🚀 Setting up Streamlit app on Mac/Linux..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi
echo "✅ Found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📥 Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the app
echo "🎬 Starting Streamlit app..."
echo "🌐 Open your browser to: http://localhost:8501"
streamlit run app.py
