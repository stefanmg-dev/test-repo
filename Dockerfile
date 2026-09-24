FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIPENV_VENV_IN_PROJECT=0 \
    EASYOCR_MODEL_STORAGE_DIRECTORY=/opt/easyocr/model \
    EASYOCR_USER_NETWORK_DIRECTORY=/opt/easyocr/user_network \
    EASYOCR_DOWNLOAD_ENABLED=false \
    HOME=/home/app \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        poppler-utils \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home app \
    && mkdir -p \
        /opt/easyocr/model \
        /opt/easyocr/user_network \
        /tmp/document-processing \
    && chown -R app:app \
        /opt/easyocr \
        /tmp/document-processing \
        /home/app

COPY Pipfile Pipfile.lock ./

RUN python -m pip install --upgrade pip pipenv \
    && pipenv sync --system \
    && python -m pip install \
        --force-reinstall \
        torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip uninstall --yes pipenv virtualenv \
    && python -m pip check

COPY docker/preload_easyocr_models.py /tmp/preload_easyocr_models.py

RUN EASYOCR_DOWNLOAD_ENABLED=true \
    python /tmp/preload_easyocr_models.py \
    && rm /tmp/preload_easyocr_models.py \
    && chown -R app:app /opt/easyocr

COPY --chown=app:app . /app

RUN chmod 0755 \
    /app/scripts/container_start.sh \
    /app/scripts/container_migrate.sh

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=3).read()"

CMD ["/app/scripts/container_start.sh"]
