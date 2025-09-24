# ---- builder: compile heavy Python deps (e.g., blis) ----
FROM python:3.9-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install build tools needed to build wheels and gunicorn
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gcc g++ make build-essential \
      python3-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip/setuptools/wheel early
RUN pip install --upgrade pip setuptools wheel

# Copy only requirements to maximize cache reuse
COPY requirements.txt .

# Build wheels for all requirements into /wheels
# The --wheel-dir flag will download and build all dependencies
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels gunicorn -r requirements.txt


# ---- final image: runtime only ----
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and prebuilt wheels
COPY requirements.txt .
COPY --from=builder /wheels /wheels

# Install from local wheelhouse only
RUN pip install --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Copy application source
COPY . /app

# Default for local testing; Cloud Run will override PORT
ENV PORT=8080

# Entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
