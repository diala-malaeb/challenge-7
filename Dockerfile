
FROM python:3.10-slim

# Prevents Python from writing .pyc files and ensures output is flushed
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (opencv headless needs these at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# The port is defined by the platform; default to 8080 for local dev
ENV PORT=8080

EXPOSE 8080

# Start with gunicorn; honor $PORT if provided
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8080} app:app --timeout 120 --workers 2 --threads 2"]
