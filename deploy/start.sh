#!/bin/sh
# Start FalkorDB in the background, wait until it answers, then run the API (which loads data/ into an empty graph).
set -e
redis-server --loadmodule /var/lib/falkordb/bin/falkordb.so --dir /app/falkordb-data \
  --bind 127.0.0.1 --port 6379 --protected-mode no --daemonize yes --logfile /app/falkordb-data/redis.log
i=0
until redis-cli -p 6379 ping >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -gt 60 ] && { echo "FalkorDB did not start"; cat /app/falkordb-data/redis.log; exit 1; }
  sleep 0.5
done
echo "FalkorDB is up"
cd /app/backend
exec /opt/venv/bin/uvicorn api:app --host 0.0.0.0 --port "${PORT:-7860}"
