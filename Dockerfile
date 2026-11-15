FROM python:3.14-slim

# uv resmi dari image Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_SYNC=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

WORKDIR /app

# Dependensi dari uv.lock (layer ter-cache selama lock tidak berubah)
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY . .

# File statis dikumpulkan saat build (nilai dummy hanya untuk build, bukan rahasia asli)
RUN SECRET_KEY=build-only DEBUG=False python manage.py collectstatic --noinput

# Jalankan sebagai user non-root
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/media \
    && chown -R app:app /app/media /app/staticfiles
USER app

EXPOSE 8000
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --access-logfile -"]
