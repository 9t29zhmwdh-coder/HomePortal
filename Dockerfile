FROM python:3.12-slim

WORKDIR /app

# The lock file pins every package with its hash, so each build installs exactly
# what was audited; a tampered or swapped download fails the build.
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

COPY app/ ./app/

# Only Nginx can reach port 8000 (compose "expose", not "ports"), so its header is trusted.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
