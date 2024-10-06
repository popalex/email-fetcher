# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt into the container
COPY ./app/requirements.txt .

# Install the required packages
RUN pip install --upgrade pip && pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of your application code into the container
COPY ./app .

# Command to run your script
CMD ["python", "app.py"]
