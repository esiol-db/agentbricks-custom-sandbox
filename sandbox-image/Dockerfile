# syntax=docker/dockerfile:1
# Custom Databricks Sandbox image for an A/B-test analyst agent.
# Ubuntu 24.04 ships glibc 2.39 and Python 3.12 out of the box.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# Put the stats stack in a venv and make it the default python3 on PATH.
# Optional: behind a TLS-inspecting proxy, pass its CA as a build secret
# (--secret id=extra_ca,src=ca.pem). It is used for pip only and never stored in a layer.
# pip reads PIP_INDEX_URL from the environment, and build args are visible to RUN as env vars,
# so `--build-arg PIP_INDEX_URL=https://mirror/simple` points the install at a mirror.
ARG PIP_INDEX_URL=https://pypi.org/simple
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -s /run/secrets/extra_ca ]; then \
      cat /etc/ssl/certs/ca-certificates.crt /run/secrets/extra_ca > /tmp/ca.pem; \
      export PIP_CERT=/tmp/ca.pem; \
    fi \
 && python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt /tmp/ca.pem
ENV PATH="/opt/venv/bin:${PATH}"

# Fail the build early if anything is missing.
RUN python3 -c "import scipy, statsmodels, pingouin, duckdb, pandas, matplotlib; print('stats stack OK')"
