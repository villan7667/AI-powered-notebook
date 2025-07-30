# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy all files into container
COPY . /app

# Create virtual environment & install dependencies
RUN python -m venv venv \
 && . venv/bin/activate \
 && pip install --upgrade pip \
 && pip install --prefer-binary -r requirements.txt

# Expose port
EXPOSE 5000

# Run the app
CMD [ "venv/bin/python", "app.py" ]
