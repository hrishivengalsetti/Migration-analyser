FROM python:3.11-slim

WORKDIR /app

# Copy requirement file and install dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application and brain module into working directory
COPY backend /app/backend
COPY brain /app/brain

ENV PYTHONPATH=/app/backend:/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
