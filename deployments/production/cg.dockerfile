# =============================================================================
# Project: Claude Guardian, unified MCP image with DB bootstrap
# File: cg.dockerfile
# =============================================================================
FROM alpine:3.20

RUN apk add --no-cache bash curl jq postgresql-client ca-certificates

WORKDIR /app

COPY init/sql/ /app/init/sql/
COPY init/qdrant/ /app/init/qdrant/
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

ENV TZ=Europe/Vienna     PGHOST=postgres     PGPORT=5432     PGUSER=cguser     PGPASSWORD=AlphaKey1234     PGDATABASE=cgdb     PG_RETRIES=50     QDRANT_URL=http://qdrant:6333     QDRANT_TIMEOUT=3     QDRANT_RETRIES=50     CG_INIT=auto     MCP_PORT=8083     MCP_CMD=""

EXPOSE 8083

ENTRYPOINT ["/app/start.sh"]
