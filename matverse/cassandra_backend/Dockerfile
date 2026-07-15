# Cassandra Backend Dockerfile
# Zero-dependency Python 3.11+ server. Stdlib only.
# No pip install needed.

FROM python:3.11-slim

WORKDIR /app

# Copy the package
COPY matverse/ /app/matverse/

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health')" || exit 1

# Run as non-root
RUN useradd -m -u 1000 cassandra
USER cassandra

EXPOSE 8787

# The CASSANDRA_API_KEY MUST be set at runtime via:
#   docker run -e CASSANDRA_API_KEY=$CASSANDRA_API_KEY ...
# Or via Docker secrets:
#   docker run --secret CASSANDRA_API_KEY ...
#
# NEVER bake the api_key into the image.

CMD ["python", "-m", "matverse.cassandra_backend.server", "--host", "0.0.0.0", "--port", "8787"]
