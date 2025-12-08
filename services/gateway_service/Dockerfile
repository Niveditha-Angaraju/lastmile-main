FROM nivedithavarma/lastmile-python-base:3.11

ENV PORT=8000 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY services/gateway_service/requirements.txt /app/requirements.txt

USER root
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --no-cache-dir -r /app/requirements.txt

USER app

COPY services/gateway_service /app/services/gateway_service
# COPY services/common_lib/protos_generated /app/services/common_lib/protos_generated

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn","services.gateway_service.app:app","--host","0.0.0.0","--port","8000"]