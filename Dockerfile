# Dockerfile (repo root)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy repo
COPY . /app

# Install deps
# 1) API deps (FastAPI + uvicorn + dotenv)
RUN pip install --no-cache-dir -r api/requirements.txt
# 2) Install core package from repo root
RUN pip install --no-cache-dir -e .

# Expose port (Railway will still inject $PORT, but this is harmless)
EXPOSE 8000

# Start (Railway sets PORT; default to 8000 if not set)
CMD ["sh", "-c", "python -m uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
