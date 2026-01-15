FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY ai_server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy common code
COPY common/ common/

ENV PYTHONPATH=/app

# Copy AI server code
COPY ai_server/app/ app/

# Run AI Worker
CMD ["python", "-m", "app.worker"]
