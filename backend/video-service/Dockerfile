FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --gecos "" appuser
COPY --from=builder /install /usr/local
COPY . .
RUN mkdir -p /app/output/audio /app/output/video /app/output/video/shorts /app/output/images && chown -R appuser:appuser /app
USER appuser
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE ${PORT:-8003}
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8003} --workers ${WORKERS:-2} --log-level ${LOG_LEVEL:-info}
