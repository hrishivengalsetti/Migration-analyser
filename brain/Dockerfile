FROM python:3.11-slim

WORKDIR /app

COPY brain/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY brain /app/brain

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "brain.main:app", "--host", "0.0.0.0", "--port", "8001"]
