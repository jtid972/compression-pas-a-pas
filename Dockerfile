# Compression pas à pas — image (linux/amd64 et linux/arm64)
# Copyright (c) 2026 Johan TIDAS — AGPL-3.0-or-later
FROM python:3.13-slim

# Numéro de version affiché (fourni par le workflow à partir de l'étiquette Git)
ARG APP_VERSION=""

# ffmpeg : vidéos · tesseract : reconnaissance de texte des PDF scannés (français + anglais)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin app

WORKDIR /srv
COPY requirements.txt .
# pip n'est utile qu'à l'installation : il est retiré ensuite (ses bibliothèques embarquées
# font partie de la surface d'attaque analysée par Trivy)
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3*/ensurepip

ENV DATA_DIR=/data \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}
RUN mkdir -p /data && chown -R app:app /data

COPY app ./app
COPY LICENSE NOTICE.md ./
USER app
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT','8000'))" || exit 1

# $PORT est fourni par Scaleway Serverless Containers ; 8000 par défaut ailleurs
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
