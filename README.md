# 🎬 ytworkflo

**YouTube Automation Platform** — A fully-typed, OpenAPI-ready FastAPI backend for automating YouTube workflows at scale.

---

## ✨ Features

| Module | Endpoints | Description |
|---|---|---|
| 🔍 **Search** | 4 | Full-text search, suggestions, related videos |
| 📹 **Video** | 7 | Full metadata, chapters, heatmap, tags, subtitle list |
| 📺 **Channel** | 4 | Info, videos, playlists, about |
| 🎬 **Playlist** | 3 | Info, videos, IDs-only |
| ⬇️ **Download** | 5 | Download to server, direct URL, serve/delete/list files |
| 🔴 **Stream** | 5 | Stream info, HLS, DASH, live stream, redirect |
| 🎵 **Audio** | 3 | Audio stream URL, extract to file, list audio formats |
| 📝 **Transcript** | 4 | Timed segments, language list, full plain text |
| 🖼️ **Thumbnails** | 4 | All resolutions, best, standard set, download |
| 📊 **Analytics** | 3 | Video metrics, channel metrics, compare vs average |
| 📦 **Batch** | 3 | Bulk video info, bulk download, bulk transcripts |
| 📋 **Formats** | 4 | All formats, filter, video-only, by extension |
| 💬 **Comments** | 4 | Top/new, POST, replies, pinned |
| 🔥 **Trending** | 3 | Trending by region/category, regions list, categories list |
| 🌐 **Subtitles** | 4 | Content, download file, serve file, available list |

**Total: 60+ endpoints**

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Install `ffmpeg` for audio extraction and format conversion:
> - macOS: `brew install ffmpeg`
> - Ubuntu: `sudo apt install ffmpeg`
> - Windows: [ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### 2. Run the server

```bash
bash run.sh
```

Or directly:

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Open the docs

| URL | Description |
|---|---|
| http://localhost:8000/docs | **Swagger UI** — interactive API explorer |
| http://localhost:8000/redoc | **ReDoc** — clean reference docs |
| http://localhost:8000/openapi.json | Raw OpenAPI 3.1 schema |

---

## 🐳 Docker

```bash
# Build and start
docker-compose up --build

# Or just build
docker build -t ytworkflo .
docker run -p 8000:8000 ytworkflo
```

---

## 📁 Project Structure

```
ytworkflo/
├── app/
│   ├── main.py                  # FastAPI app, middleware, router registration
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env-driven)
│   │   └── exceptions.py        # Custom exceptions + handlers
│   ├── models/
│   │   └── schemas.py           # All Pydantic request/response models
│   ├── services/
│   │   └── ytdlp_service.py     # yt-dlp wrapper (central extraction layer)
│   ├── routers/
│   │   ├── search.py            # /api/v1/search
│   │   ├── video.py             # /api/v1/video
│   │   ├── channel.py           # /api/v1/channel
│   │   ├── playlist.py          # /api/v1/playlist
│   │   ├── download.py          # /api/v1/download
│   │   ├── stream.py            # /api/v1/stream
│   │   ├── audio.py             # /api/v1/audio
│   │   ├── transcript.py        # /api/v1/transcript
│   │   ├── thumbnails.py        # /api/v1/thumbnails
│   │   ├── analytics.py         # /api/v1/analytics
│   │   ├── batch.py             # /api/v1/batch
│   │   ├── formats.py           # /api/v1/formats
│   │   ├── comments.py          # /api/v1/comments
│   │   ├── trending.py          # /api/v1/trending
│   │   └── subtitles.py         # /api/v1/subtitles
│   └── utils/
├── tests/
│   └── test_api.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── run.sh
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and adjust:

```env
DEBUG=false
CORS_ORIGINS=["https://yourfrontend.com"]
DOWNLOAD_DIR=/data/downloads
AUDIO_DIR=/data/audio
SUBTITLE_DIR=/data/subtitles
THUMBNAIL_DIR=/data/thumbnails
YTDLP_SOCKET_TIMEOUT=30
YTDLP_RETRIES=3
```

---

## 🧪 Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 📡 API Examples

### Search
```bash
GET /api/v1/search?q=python+tutorial&per_page=10
```

### Video info
```bash
GET /api/v1/video/dQw4w9WgXcQ
```

### Download direct URL
```bash
GET /api/v1/download/url/dQw4w9WgXcQ?quality=720p
```

### Get transcript
```bash
GET /api/v1/transcript/dQw4w9WgXcQ?language=en
```

### Batch video info
```bash
POST /api/v1/batch/videos
{"video_ids": ["dQw4w9WgXcQ", "jNQXAC9IVRw"]}
```

### Trending (India, Music)
```bash
GET /api/v1/trending?region=IN&category=10
```

---

## 🔧 Tech Stack

- **FastAPI** — async web framework with automatic OpenAPI generation
- **Pydantic v2** — full request/response validation and serialization
- **yt-dlp** — powerful YouTube extraction engine
- **ffmpeg** — audio/video processing
- **uvicorn** — ASGI server

---

## 📄 License

MIT
