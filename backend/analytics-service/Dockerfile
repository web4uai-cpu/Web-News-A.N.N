FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13-slim
WORKDIR /app
RUN adduser --disabled-password --gecos "" appuser
COPY --from=builder /install /usr/local
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE ${PORT:-8005}
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8005} --workers ${WORKERS:-2} --log-level ${LOG_LEVEL:-info}
