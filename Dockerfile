# Use a modern slim base image
FROM python:3.10-slim-bookworm

# Set working directory inside the container
WORKDIR /app

# Install only required system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files into container
COPY . /app

# Set up virtual environment & install dependencies
RUN python -m venv venv \
 && . venv/bin/activate \
 && pip install --upgrade pip \
 && pip install --prefer-binary -r requirements.txt

# Expose the port Flask will run on
EXPOSE 5000

# Start the Flask app
CMD ["venv/bin/python", "app.py"]
