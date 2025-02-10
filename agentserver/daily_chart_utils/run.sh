mkdir -p ./daily_chart_utils/logs

gunicorn daily_chart_utils.utils:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 2 \
  --bind 0.0.0.0:30826 \
  --timeout 300 \
  --log-level info \
  --access-logfile ./daily_chart_utils/logs/access.log \
  --error-logfile ./daily_chart_utils/logs/error.log 