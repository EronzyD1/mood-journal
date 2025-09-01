# Dockerfile for Flask + Gunicorn
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Work directory inside container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment port (Cloud Run uses $PORT)
ENV PORT=8080

# Start Gunicorn server
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4
