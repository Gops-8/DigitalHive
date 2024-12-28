# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p input output/analysis output/cache

# Set environment variables
ENV PYTHONPATH=/app
ENV OLLAMA_URL=http://host.docker.internal:11434

# Expose port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "src/web/app.py"]
