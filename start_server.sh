#!/bin/bash

# Display Start Message
echo "========================================"
echo "  Starting/Rebooting DigitalHive App"
echo "========================================"

# Navigate to Project Directory
echo "Navigating to project directory..."

# Activate Virtual Environment
VENV_DIR="venv"

# Attempt to activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate" 2>/dev/null || {
    echo "Virtual environment not found. Creating a new one..."

    # Create a new virtual environment
    python3 -m venv "$VENV_DIR" || { echo "Failed to create virtual environment"; exit 1; }

    # Activate the newly created virtual environment
    source "$VENV_DIR/bin/activate" || { echo "Failed to activate the newly created virtual environment"; exit 1; }

    # Install required Python packages
    echo "Installing required Python packages..."
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt || { echo "Failed to install packages"; exit 1; }
    else
        echo "No requirements.txt found. Skipping package installation."
    fi
}

echo "Virtual environment is activated and ready!"


# Pull Latest Changes
echo "Pulling latest changes from repository..."

# Fetch the latest changes
git fetch https://github.com/Gops-8/DigitalHive.git || { echo "Failed to fetch changes"; exit 1; }

# Reset local changes and force match to the remote branch
git reset --hard origin/$(git rev-parse --abbrev-ref HEAD) || { echo "Failed to reset local changes"; exit 1; }

echo "Successfully synchronized with the remote repository, keeping remote changes!"


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
