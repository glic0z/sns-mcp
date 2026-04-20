FROM python:3.11-slim

LABEL maintainer="glicoz"
LABEL description="Read-only MCP server for Stormshield SNS firewalls"

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Copy config example
COPY config/config.example.yaml ./config/config.example.yaml

# Switch to non-root user
USER appuser

# Config volume mount point
VOLUME ["/app/config"]

# HTTP mode port
EXPOSE 8765

# Health check using the device list tool
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from stormshield_mcp.config.loader import load_config; load_config('/app/config/config.yaml')" || exit 1

# Default: STDIO mode. Override CMD for HTTP mode.
ENTRYPOINT ["stormshield-mcp"]
CMD ["--config", "/app/config/config.yaml"]
