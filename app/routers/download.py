import os
import uuid

from fastapi import APIRouter, Path, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.exceptions import ExtractionError
from app.models.schemas import (
    AudioFormat,
    DownloadRequest,
    DownloadResponse,
    DownloadURLResponse,
    VideoQuality,
)
from app.services import ytdlp_service as svc

router = APIRouter()


def _quality_to_format(quality: VideoQuality, audio_only: bool = False) -> str:
    if audio_only:
        return "bestaudio/best"
    if quality == VideoQuality.best:
        return "bestvideo+bestaudio/best"
    if quality == VideoQuality.worst:
        return "worstvideo+worstaudio/worst"
    h = quality.value.replace("p", "")
    return f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"


@router.post(
    "",
    response_model=DownloadResponse,
    summary="Download video/audio",
    description="Download a YouTube video or audio to the server's download directory.",
)
async def download_video(req: DownloadRequest):
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    fmt = _quality_to_format(req.quality, audio_only=req.audio_only)
    if req.format_id:
        fmt = req.format_id

    post_processors = []
    if req.audio_only:
        post_processors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": req.audio_format.value,
        })
    if req.embed_thumbnail:
        post_processors.append({"key": "EmbedThumbnail"})
    if req.add_metadata:
        post_processors.append({"key": "FFmpegMetadata"})

    opts = {
        "format": fmt,
        "postprocessors": post_processors,
        "writethumbnail": req.embed_thumbnail,
        "writesubtitles": req.embed_subs,
        "subtitleslangs": [req.subtitle_lang] if req.subtitle_lang else [],
    }

    result = svc.download_video(req.video_id, opts)
    info = result["info"]
    filename = result["filename"]
    filepath = filename

    ext = info.get("ext", "mp4")
    if req.audio_only:
        ext = req.audio_format.value

    return DownloadResponse(
        task_id=result["task_id"],
        video_id=info.get("id", req.video_id),
        title=info.get("title", ""),
        filename=os.path.basename(filename),
        filepath=filepath,
        filesize=os.path.getsize(filepath) if os.path.exists(filepath) else None,
        format=fmt,
        ext=ext,
        status="completed",
    )


@router.get(
    "/url/{video_id}",
    response_model=DownloadURLResponse,
    summary="Get direct download URL",
    description="Returns a direct CDN URL for the video without downloading to server.",
)
async def get_download_url(
    video_id: str = Path(...),
    quality: VideoQuality = Query(VideoQuality.best),
    format_id: str = Query(None),
):
    result = svc.get_direct_url(video_id, format_id=format_id, quality=quality.value)
    return DownloadURLResponse(
        video_id=result["video_id"],
        title=result["title"],
        direct_url=result["direct_url"],
        ext=result["ext"],
        format_id=result["format_id"],
        filesize=result.get("filesize"),
        expires_approx="~6 hours (CDN token)",
    )


@router.get(
    "/file/{filename}",
    summary="Serve downloaded file",
    description="Serve a previously downloaded file by filename.",
)
async def serve_file(filename: str = Path(...)):
    filepath = os.path.join(settings.DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, filename=filename)


@router.delete(
    "/file/{filename}",
    summary="Delete downloaded file",
)
async def delete_file(filename: str = Path(...)):
    filepath = os.path.join(settings.DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"deleted": True, "filename": filename}
    return {"deleted": False, "filename": filename, "reason": "not found"}


@router.get(
    "/list",
    summary="List downloaded files",
    description="Lists all files currently in the download directory.",
)
async def list_downloads():
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    files = []
    for f in os.listdir(settings.DOWNLOAD_DIR):
        fp = os.path.join(settings.DOWNLOAD_DIR, f)
        files.append({
            "filename": f,
            "size": os.path.getsize(fp),
            "modified": os.path.getmtime(fp),
        })
    return {"files": files, "total": len(files)}
