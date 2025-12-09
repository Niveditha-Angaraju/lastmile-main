FROM python:3.11-slim

WORKDIR /app
COPY services/gateway_service/requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/gateway_service /app/services/gateway_service
COPY services/common_lib/protos_generated /app/services/common_lib/protos_generated

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["python", "-u", "services/gateway_service/app.py"]
