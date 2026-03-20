# Use the official Python Alpine/Slim image for a tiny, ultra-fast container
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies utilizing Docker cache efficiently
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY . .

# Expose port (Railway dynamically injects $PORT but defaults to 8000 locally)
EXPOSE 8000

# Command to run the high-performance ASGI server for WebSockets & APIs
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
