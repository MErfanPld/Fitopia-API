# Fitopia API — production image
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (Pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libpng-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY req.txt /app/req.txt
RUN pip install --upgrade pip \
    && pip install -r req.txt \
    && pip install gunicorn==23.0.0 whitenoise==6.9.0

# App code
COPY . /app/

# Directories for runtime data
RUN mkdir -p /app/media /app/staticfiles /app/data \
    && chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
