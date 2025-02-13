mkdir -p ./logs

gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 2 \
  --bind 0.0.0.0:30820 \
  --timeout 300 \
  --log-level info \
  --access-logfile ./logs/access.log \
  --error-logfile ./logs/error.log