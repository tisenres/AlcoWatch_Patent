#!/bin/bash

# AlcoWatch Quick Simulation Launcher
# No hardware required - runs complete system simulation

echo "=========================================="
echo "  AlcoWatch System Simulator"
echo "  No Hardware Required"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Navigate to simulation directory
cd "$(dirname "$0")/arduino/simulation"

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import asyncio" 2>/dev/null; then
    echo "❌ asyncio not available"
    exit 1
fi

echo "✓ All dependencies available"
echo ""

# Run the simulation
echo "Starting simulation..."
echo ""
python3 run_simulation.py

echo ""
echo "=========================================="
echo "  Simulation Complete"
echo "=========================================="
