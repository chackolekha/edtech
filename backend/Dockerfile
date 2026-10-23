FROM python:3.13-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt "psycopg[binary]>=3.2"

COPY . .

EXPOSE 8000

# Apply migrations, then serve. SQLite default works without the db service;
# Postgres is used when DATABASE_URL points at the compose `db` service.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
