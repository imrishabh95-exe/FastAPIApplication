# Start with a lightweight Python base image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY ./Application ./Application

# Expose the app port
EXPOSE 8080

# Use entrypoint script if you have one, or run with correct module path
CMD ["uvicorn", "Application.main:app", "--host", "0.0.0.0", "--port", "8080"]
