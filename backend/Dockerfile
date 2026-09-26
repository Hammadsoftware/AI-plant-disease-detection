# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ARG TORCH_INDEX_URL

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# CPU-only torch first, so requirements.txt finds the installed versions and never
# pulls the CUDA build (which adds ~2.5GB of shared libraries to the image).
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install --index-url ${TORCH_INDEX_URL} torch torchvision \
    && /opt/venv/bin/pip install -r requirements.txt


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    APP_USER=appuser \
    MODEL_PATH=/app/models/efficientnet_v2_s_best.torchscript.pt \
    CLASS_LABELS_PATH=/app/models/class_labels.json \
    UPLOAD_DIR=/app/uploads \
    STORE_UPLOADS=true

# libgomp1 provides the OpenMP runtime torch links against.
# gosu lets the entrypoint fix bind-mount ownership and then drop privileges.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 gosu curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 appuser \
    && useradd --system --uid 1001 --gid appuser --create-home --home-dir /home/appuser appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR ${APP_HOME}

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser tests ./tests
COPY --chown=root:root entrypoint.sh /usr/local/bin/entrypoint.sh

# The checkpoint and class labels are baked in so the API starts on platforms that
# do not bind mount a host directory (Render, for example). MODEL_PATH and
# CLASS_LABELS_PATH above already point here. A host mount on /app/models still
# overrides these files at runtime, so local development is unchanged.
COPY --chown=appuser:appuser models ./models

RUN mkdir -p "${APP_HOME}/uploads" \
    && chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

# The model is loaded during lifespan startup, so allow a long start period.
# The health route also probes Groq and the search provider.
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD ["python", "-c", "import os, sys, urllib.request; url = 'http://127.0.0.1:8000' + os.environ.get('API_PREFIX', '/api/v1') + '/health'; sys.exit(0 if urllib.request.urlopen(url, timeout=10).status == 200 else 1)"]

# One uvicorn worker on purpose: the checkpoint is loaded per worker and
# MAX_CONCURRENT_INFERENCES serializes inference inside a worker.
# Scale with replicas, not workers.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
