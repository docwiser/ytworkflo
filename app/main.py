"""
ytworkflo - YouTube Automation Platform
FastAPI backend with OpenAPI/Swagger docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.routers import (
    search,
    video,
    channel,
    playlist,
    download,
    stream,
    audio,
    transcript,
    thumbnails,
    analytics,
    batch,
    formats,
    comments,
    trending,
    subtitles,
)

app = FastAPI(
    title="ytworkflo",
    description="""
## 🎬 ytworkflo — YouTube Automation Platform

A powerful, fully-typed FastAPI backend for automating YouTube workflows.

### Features
- 🔍 **Search** — Full-text search with filters, sorting, and pagination
- 📹 **Video Info** — Metadata, stats, formats, chapters, thumbnails
- 📺 **Channel** — Channel info, videos, playlists, community posts
- 🎵 **Audio** — Extract audio, convert formats, get waveform info
- 📝 **Transcripts** — Auto/manual captions, translation, timestamped segments
- ⬇️ **Download** — Download video/audio with quality selection
- 🔴 **Stream** — Proxy streaming URLs, live stream detection
- 📊 **Analytics** — Engagement metrics, estimated reach, performance scores
- 🖼️ **Thumbnails** — Fetch all thumbnail resolutions
- 💬 **Comments** — Top/recent comments, replies, sentiment
- 📦 **Batch** — Bulk operations on multiple videos/channels
- 🔥 **Trending** — Trending videos by region and category
- 🌐 **Subtitles** — Download/convert subtitle formats (VTT, SRT, JSON)
- 📋 **Formats** — List all available formats for a video
""",
    version="1.0.0",
    contact={"name": "ytworkflo", "url": "https://github.com/ytworkflo"},
    license_info={"name": "MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(search.router,      prefix="/api/v1/search",      tags=["Search"])
app.include_router(video.router,       prefix="/api/v1/video",        tags=["Video"])
app.include_router(channel.router,     prefix="/api/v1/channel",      tags=["Channel"])
app.include_router(playlist.router,    prefix="/api/v1/playlist",     tags=["Playlist"])
app.include_router(download.router,    prefix="/api/v1/download",     tags=["Download"])
app.include_router(stream.router,      prefix="/api/v1/stream",       tags=["Stream"])
app.include_router(audio.router,       prefix="/api/v1/audio",        tags=["Audio"])
app.include_router(transcript.router,  prefix="/api/v1/transcript",   tags=["Transcript"])
app.include_router(thumbnails.router,  prefix="/api/v1/thumbnails",   tags=["Thumbnails"])
app.include_router(analytics.router,  prefix="/api/v1/analytics",    tags=["Analytics"])
app.include_router(batch.router,       prefix="/api/v1/batch",        tags=["Batch"])
app.include_router(formats.router,     prefix="/api/v1/formats",      tags=["Formats"])
app.include_router(comments.router,    prefix="/api/v1/comments",     tags=["Comments"])
app.include_router(trending.router,    prefix="/api/v1/trending",     tags=["Trending"])
app.include_router(subtitles.router,   prefix="/api/v1/subtitles",    tags=["Subtitles"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"], summary="Health check")
async def health():
    """Returns platform health status."""
    return {"status": "ok", "platform": "ytworkflo", "version": "1.0.0"}
