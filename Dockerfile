FROM python:3.11-slim

# Install system dependencies (ffmpeg for audio/video processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create working directories
RUN mkdir -p /tmp/ytworkflo/downloads \
             /tmp/ytworkflo/audio \
             /tmp/ytworkflo/subtitles \
             /tmp/ytworkflo/thumbnails

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
