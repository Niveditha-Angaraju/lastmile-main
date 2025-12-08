FROM lastmile/python-base:3.11
ENV PORT=8007 PYTHONPATH=/app
WORKDIR /app
COPY services/trip_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/trip_service_service /app/services/trip_service
COPY services/common_lib/protos_generated /app/services/common_lib/protos_generated
EXPOSE 8007
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import socket,os,sys,socket as _s; s=_s.socket();\
try: s.settimeout(2); s.connect(('127.0.0.1', int(os.getenv('PORT','8006')))); s.close(); sys.exit(0) \
except: sys.exit(1)"
CMD ["python", "-u", "services/trip_service/app.py"]
