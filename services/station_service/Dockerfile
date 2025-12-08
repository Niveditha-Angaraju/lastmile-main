FROM nivedithavarma/lastmile-python-base:3.11
ENV PORT=8005 PYTHONPATH=/app
WORKDIR /app
COPY services/station_service/requirements.txt /app/requirements.txt
USER root
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /app/requirements.txt
USER app
COPY services/station_service /app/services/station_service
COPY services/common_lib/protos_generated /app/services/common_lib/protos_generated
EXPOSE 8005
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import socket,os,sys;s=socket.socket();\
try: s.settimeout(2); s.connect(('127.0.0.1', int(os.getenv('PORT','8005')))); s.close(); sys.exit(0) \
except: sys.exit(1)"
CMD ["python", "-u", "services/station_service/app.py"]

