# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY requirements.txt .
COPY app.py .
COPY models/ ./models/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose API port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
