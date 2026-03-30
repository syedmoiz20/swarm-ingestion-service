FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY ingestion_service /app/ingestion_service
COPY shared /app/shared
COPY worker /app/worker
COPY scripts /app/scripts
COPY main.py /app/main.py

RUN chmod +x /app/scripts/*.sh

EXPOSE 8080

CMD ["/app/scripts/start_api.sh"]
