# Single container: FalkorDB + Bouncer API + website on one port (7860, the Hugging Face Spaces default).
# Build:  docker build -t bouncer .        Run:  docker run -p 7860:7860 bouncer   -> http://localhost:7860

# ---- 1. build the React website (API calls go to the same origin: VITE_API_URL=/)
FROM node:20-slim AS web
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci
COPY frontend frontend
COPY contracts contracts
COPY data data
RUN cd frontend && VITE_API_URL=/ VITE_USE_MOCKS=false npm run build

# ---- 2. FalkorDB image + Python API
# Pinned: 'latest' currently points at the older 4.22 line, where a variable-length path with an
# inline end-node filter returns nothing. Everything was built and tested on 6.0.1.
FROM falkordb/falkordb:6.0.1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir \
    "falkordb>=1.8" "fastapi>=0.115" "uvicorn>=0.30" "pydantic>=2.9" "python-dotenv>=1.0"

WORKDIR /app
COPY backend backend
COPY data data
COPY --from=web /src/frontend/dist frontend/dist
COPY deploy/start.sh deploy/start.sh

# Hugging Face runs the container as uid 1000: give it the folders it writes to.
# (not /data: the FalkorDB image declares it a volume, so ownership changes there are discarded)
RUN mkdir -p /app/falkordb-data && chown -R 1000:1000 /app && chmod +x deploy/start.sh

ENV FALKORDB_HOST=127.0.0.1 FALKORDB_PORT=6379 THREAT_GRAPH=threat \
    FRONTEND_DIST=/app/frontend/dist CORS_ORIGINS=http://localhost:7860 PORT=7860
EXPOSE 7860
USER 1000
ENTRYPOINT []
CMD ["/app/deploy/start.sh"]
