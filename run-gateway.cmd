@echo off
rem Start the rescue-center gateway over HTTPS on port 8443.
cd /d "%~dp0"
if not exist certs\cert.pem .venv\Scripts\python.exe gateway\make_cert.py
.venv\Scripts\python.exe -m uvicorn gateway.server:app --host 0.0.0.0 --port 8443 --ssl-keyfile certs\key.pem --ssl-certfile certs\cert.pem
