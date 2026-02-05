FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/scalers/ ./src/scalers/
COPY src/utils/ ./src/utils/
COPY src/config.py ./src/
COPY models/ ./models/

EXPOSE 50051

CMD ["python", "-m", "src.scalers.keda_grpc_server"]