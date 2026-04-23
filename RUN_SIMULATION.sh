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
echo "Available scenarios:"
echo "  BAC Detection:   1=Sober  2=Intoxicated  3=Tamper  4=Drinking  5=Edge  6=All BAC"
echo "  Stress Detection: 7=Highway  8=Traffic  9=Panic  10=Fatigue  11=Watch removed  12=All stress"
echo ""
echo "Starting simulation..."
echo ""
python3 run_simulation.py

echo ""
echo "=========================================="
echo "  Simulation Complete"
echo "=========================================="
