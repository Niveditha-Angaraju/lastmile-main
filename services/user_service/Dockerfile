FROM nivedithavarma/lastmile-python-base:3.11
ENV PORT=8001 PYTHONPATH=/app
WORKDIR /app
COPY services/user_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/user_service /app/services/user_service
COPY services/common_lib/protos_generated /app/services/common_lib/protos_generated
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import socket,os,sys;s=socket.socket();\
try: s.settimeout(2); s.connect(('127.0.0.1', int(os.getenv('PORT','8001')))); s.close(); sys.exit(0) \
except: sys.exit(1)"
CMD ["python", "-u", "services/user_service/app.py"]
