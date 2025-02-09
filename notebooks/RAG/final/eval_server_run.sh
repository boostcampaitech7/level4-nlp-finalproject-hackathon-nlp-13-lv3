mkdir -p ./logs

gunicorn financial_reports_rag_api:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 2 \
  --bind 0.0.0.0:30800 \
  --log-level debug \
  --access-logfile ./logs/access.log \
  --error-logfile ./logs/error.log