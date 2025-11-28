FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY infrastructure/ infrastructure/
CMD ["celery", "-A", "infrastructure.celery_app.celery", "worker", "-l", "info"]
