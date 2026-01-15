FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY api_server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy common code
COPY common/ common/

ENV PYTHONPATH=/app

# Copy API server code
COPY api_server/app/ app/

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
