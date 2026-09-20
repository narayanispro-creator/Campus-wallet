FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE_PATH=/data/wallet.sqlite3 PORT=8080
COPY requirements.txt requirements-hosting.txt ./
RUN pip install --no-cache-dir -r requirements-hosting.txt && useradd --create-home wallet && mkdir /data && chown wallet:wallet /data
COPY --chown=wallet:wallet app.py ./
COPY --chown=wallet:wallet templates ./templates
COPY --chown=wallet:wallet static ./static
USER wallet
EXPOSE 8080
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --access-logfile - 'app:create_app()'"]
