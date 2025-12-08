FROM nivedithavarma/lastmile-python-base:3.11
ENV PORT=50053 PYTHONPATH=/app
WORKDIR /app
COPY services/location_service/requirements.txt /app/requirements.txt
USER root
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /app/requirements.txt
USER app
COPY services/location_service /app/services/location_service
COPY services/common_lib/protos_generated /app/services/common_lib/protos_generated
EXPOSE 50053
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import socket,os,sys;s=socket.socket();\
try: s.settimeout(2); s.connect(('127.0.0.1', int(os.getenv('PORT','50053')))); s.close(); sys.exit(0) \
except: sys.exit(1)"
CMD ["python", "-u", "services/location_service/app.py"]
