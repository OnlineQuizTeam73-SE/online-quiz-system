FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DATABASE_PATH=/data/quiz.db \
    PORT=8000

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /data \
    && chown app:app /data

COPY Sprint2_S2-01_S2-14/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app Sprint2_S2-01_S2-14/app.py ./app.py
COPY --chown=app:app Sprint2_S2-01_S2-14/schema.sql ./schema.sql
COPY --chown=app:app Sprint2_S2-01_S2-14/templates ./templates
COPY --chown=app:app Sprint2_S2-01_S2-14/static ./static
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0555 /usr/local/bin/docker-entrypoint.sh

USER app
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
