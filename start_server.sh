#!/bin/bash

# Activate the virtual environment
source ../dev/bin/activate

# Navigate to the project directory
# cd ~/work/market_analysis

# Set PYTHONPATH to include the src directory
export PYTHONPATH=$(pwd)

# Start the server
st src/web/app.py
