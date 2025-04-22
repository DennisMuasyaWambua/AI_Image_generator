FROM python:3.8-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create output and datastore directories
RUN mkdir -p output datastore

# Expose port 8888
EXPOSE 8888

# Start the application using our direct Flask app
CMD ["python3", "app.py"]