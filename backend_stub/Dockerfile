FROM python:3.11-slim

WORKDIR /app

COPY backend_stub/requirements.txt /app/backend_stub/requirements.txt
RUN pip install --no-cache-dir -r /app/backend_stub/requirements.txt

RUN groupadd --gid 10001 datavision \
    && useradd --uid 10001 --gid datavision --create-home datavision

COPY --chown=datavision:datavision backend_stub /app/backend_stub
COPY --chown=datavision:datavision ai /app/ai
COPY --chown=datavision:datavision outputs/ui_fixtures /app/outputs/ui_fixtures

ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000
ENV DATAVISION_BACKEND_MODE=staging
ENV RAG_EMBEDDING_MODE=hash

EXPOSE 8000

USER datavision

CMD ["sh", "-c", "uvicorn backend_stub.main:app --host ${BACKEND_HOST} --port ${BACKEND_PORT}"]
