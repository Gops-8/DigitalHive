#!/bin/bash

# Display Start Message
echo "========================================"
echo "  Starting/Rebooting DigitalHive App"
echo "========================================"

# Navigate to Project Directory
echo "Navigating to project directory..."

# Activate Virtual Environment
echo "Activating virtual environment..."
source venv/bin/activate || { echo "Failed to activate venv"; exit 1; }


# Pull Latest Changes
echo "Pulling latest changes from repository..."

echo "Stashing local changes..."
git stash push -m "Auto stash before pulling latest changes" || { echo "Failed to stash changes"; exit 1; }

echo "Pulling latest changes from repository..."
git pull https://github.com/Gops-8/DigitalHive.git || { echo "Failed to pull latest changes"; exit 1; }

echo "Applying stashed changes..."
git stash apply || { echo "No stashed changes to apply"; }

echo "Successfully pulled and applied local changes!"

# Check if Port 8501 is in Use
echo "Checking if Streamlit server is running on port 8501..."
PORT=8501
PID=$(lsof -i:$PORT -t)

if [ -n "$PID" ]; then
  echo "Streamlit server is running on port $PORT. Stopping it..."
  kill -9 $PID || { echo "Failed to stop the process"; exit 1; }
  echo "Streamlit server stopped."
else
  echo "No process found running on port $PORT."
fi

# Start the Streamlit Server
echo "Starting Streamlit server..."
streamlit run src/web/app.py --server.port=$PORT|| { echo "Failed to start the Streamlit server"; exit 1; }

# Final Message
echo "========================================"
echo "  DigitalHive App is now running."
echo "========================================"
