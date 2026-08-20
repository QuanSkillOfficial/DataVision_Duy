FROM python:3.11-slim

WORKDIR /app

COPY demo/requirements-ci.txt /app/demo/requirements-ci.txt
RUN pip install --no-cache-dir -r /app/demo/requirements-ci.txt

RUN groupadd --gid 10001 datavision \
    && useradd --uid 10001 --gid datavision --create-home datavision

COPY --chown=datavision:datavision demo /app/demo

ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

USER datavision

CMD ["streamlit", "run", "demo/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
