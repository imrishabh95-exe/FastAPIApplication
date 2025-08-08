# Start with a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY ./Application .

# Expose the port on which the app will run (default for Uvicorn)
EXPOSE 8000

WORKDIR /app/Application

# Command to run the application with Uvicorn
# The exec form is preferred to ensure graceful shutdowns
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]