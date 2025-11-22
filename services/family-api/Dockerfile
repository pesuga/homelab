FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
RUN chmod -R 755 /app/src

# Create uploads directory with proper permissions for non-root user
RUN mkdir -p /app/uploads && chown -R 1000:1000 /app/uploads

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application (without --reload for production stability)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
