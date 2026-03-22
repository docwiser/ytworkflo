"""Batch router"""
import asyncio
from typing import List, Union
from fastapi import APIRouter, Query
from app.models.schemas import (
    BatchVideoRequest, BatchVideoResponse, BatchDownloadRequest,
    BatchDownloadResponse, BatchTranscriptRequest, VideoInfo, DownloadResponse, AudioFormat
)
from app.services import ytdlp_service as svc
from app.routers.video import _build_video_info

router = APIRouter()


@router.post("/videos", response_model=BatchVideoResponse, summary="Batch get video info",
             description="Fetch metadata for up to 50 videos in one request.")
async def batch_get_videos(req: BatchVideoRequest):
    results = []
    succeeded = 0
    failed = 0
    for vid in req.video_ids:
        try:
            url = svc.normalize_id(vid)
            info = svc.extract_info(url)
            results.append(_build_video_info(info, include_formats=req.include_formats))
            succeeded += 1
        except Exception as e:
            results.append({"video_id": vid, "error": str(e)})
            failed += 1
    return BatchVideoResponse(requested=len(req.video_ids), succeeded=succeeded, failed=failed, results=results)


@router.post("/download", response_model=BatchDownloadResponse, summary="Batch download",
             description="Queue download for up to 20 videos.")
async def batch_download(req: BatchDownloadRequest):
    import uuid
    task_id = str(uuid.uuid4())
    items = []
    for vid in req.video_ids:
        try:
            pp = [{"key": "FFmpegExtractAudio", "preferredcodec": req.audio_format.value}] if req.audio_only else []
            fmt = "bestaudio/best" if req.audio_only else "bestvideo+bestaudio/best"
            result = svc.download_video(vid, {"format": fmt, "postprocessors": pp})
            info = result["info"]
            import os
            fp = result["filename"]
            items.append(DownloadResponse(
                task_id=result["task_id"], video_id=info.get("id", vid),
                title=info.get("title", ""), filename=os.path.basename(fp), filepath=fp,
                filesize=os.path.getsize(fp) if os.path.exists(fp) else None,
                format=fmt, ext=req.audio_format.value if req.audio_only else info.get("ext","mp4"),
                status="completed",
            ))
        except Exception as e:
            items.append(DownloadResponse(
                task_id="error", video_id=vid, title="", filename="", filepath="",
                format="", ext="", status="failed", message=str(e),
            ))
    return BatchDownloadResponse(task_id=task_id, requested=len(req.video_ids),
                                  status="completed", items=items)


@router.post("/transcripts", summary="Batch get transcripts",
             description="Fetch transcripts for up to 20 videos.")
async def batch_transcripts(req: BatchTranscriptRequest):
    results = []
    for vid in req.video_ids:
        try:
            url = svc.normalize_id(vid)
            result = svc.get_subtitles_content(url, lang=req.language, fmt="vtt", auto=req.auto_generated)
            info = result.get("info") or {}
            results.append({"video_id": info.get("id", vid), "title": info.get("title", ""),
                             "has_transcript": bool(result.get("content")), "status": "ok"})
        except Exception as e:
            results.append({"video_id": vid, "status": "error", "error": str(e)})
    return {"requested": len(req.video_ids), "results": results}
