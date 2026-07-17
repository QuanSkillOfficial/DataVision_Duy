FROM python:3.11-slim

WORKDIR /app

COPY backend_stub/requirements.txt /app/backend_stub/requirements.txt
RUN pip install --no-cache-dir -r /app/backend_stub/requirements.txt

COPY backend_stub /app/backend_stub
COPY outputs/ui_fixtures /app/outputs/ui_fixtures

ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend_stub.main:app --host ${BACKEND_HOST} --port ${BACKEND_PORT}"]
