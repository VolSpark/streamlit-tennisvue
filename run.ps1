#!/usr/bin/env pwsh
# run.ps1 - Windows PowerShell 7+ script to set up and run the Streamlit app
# Usage: .\run.ps1

Write-Host "🚀 Setting up Streamlit app on Windows..." -ForegroundColor Green

# Check if Python is installed
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Found: $pythonCheck" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-Not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "📥 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run the app
Write-Host "🎬 Starting Streamlit app..." -ForegroundColor Green
Write-Host "🌐 Open your browser to: http://localhost:8501" -ForegroundColor Cyan
streamlit run app.py
