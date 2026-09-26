FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY samples /app/samples
RUN mkdir -p /data/uploads

ENV DATABASE_URL=sqlite:////data/leaseflow.db
ENV STORAGE_DIR=/data/uploads
ENV SAMPLES_DIR=/app/samples

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
