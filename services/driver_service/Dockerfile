FROM nivedithavarma/lastmile-python-base:3.11

ENV PORT=50052 PYTHONPATH=/app
WORKDIR /app
COPY services/driver_service/requirements.txt /app/requirements.txt
USER root
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /app/requirements.txt
USER app
COPY services/driver_service /app/services/driver_service
COPY services/common_lib/protos_generated /app/services/common_lib/protos_generated
EXPOSE 50052
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import socket,os,sys;s=socket.socket();\
try: s.settimeout(2); s.connect(('127.0.0.1', int(os.getenv('PORT','50052')))); s.close(); sys.exit(0) \
except: sys.exit(1)"
CMD ["python", "-u", "services/driver_service/app.py"]

