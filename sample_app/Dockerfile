FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY app.py .
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]