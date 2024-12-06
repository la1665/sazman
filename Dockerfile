FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install necessary system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    postgresql-client \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy and ensure the `wait-for-db.sh` script is executable
COPY wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/wait-for-db.sh

# Create the logs directory with appropriate permissions
RUN mkdir -p logs && chmod 755 logs

# Expose application port
EXPOSE 8000

# Command to start the app with `wait-for-db.sh`
CMD ["uvicorn", "main:app_socket", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "debug"]
# CMD ["./wait-for-db.sh", "db", "uvicorn", "main:app_socket", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "debug"]
