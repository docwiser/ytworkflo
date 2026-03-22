"""Audio router"""
import os
from fastapi import APIRouter, Path, Query
from app.models.schemas import AudioExtractRequest, AudioInfo, AudioStreamInfo, AudioStreamRequest, AudioFormat
from app.services import ytdlp_service as svc
from app.core.config import settings

router = APIRouter()


@router.get("/{video_id}/stream", response_model=AudioStreamInfo, summary="Get audio stream URL",
            description="Returns direct audio-only streaming URL.")
async def get_audio_stream(video_id: str = Path(...), fmt: AudioFormat = Query(AudioFormat.best)):
    url = svc.normalize_id(video_id)
    af = "bestaudio/best" if fmt == AudioFormat.best else f"bestaudio[ext={fmt.value}]/bestaudio/best"
    info = svc.extract_info(url, {"format": af})
    fmts = [f for f in (info.get("formats") or []) if f.get("acodec") and f.get("acodec") != "none"]
    sel = fmts[-1] if fmts else {}
    return AudioStreamInfo(
        video_id=info.get("id", video_id),
        title=info.get("title", ""),
        stream_url=sel.get("url") or info.get("url", ""),
        ext=sel.get("ext") or info.get("ext", ""),
        abr=sel.get("abr"),
        asr=sel.get("asr"),
        acodec=sel.get("acodec"),
    )


@router.post("/extract", response_model=AudioInfo, summary="Extract audio to file",
             description="Download and extract audio from a video to the server.")
async def extract_audio(req: AudioExtractRequest):
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    pp = [{"key": "FFmpegExtractAudio", "preferredcodec": req.format.value,
            "preferredquality": req.quality}]
    if req.normalize:
        pp.append({"key": "FFmpegNormalize"})
    opts = {"format": "bestaudio/best", "postprocessors": pp}
    if req.start_time or req.end_time:
        sections = f"*{req.start_time or 0}-{req.end_time or 'inf'}"
        opts["download_ranges"] = lambda _, __: [{"start_time": req.start_time or 0,
                                                   "end_time": req.end_time}]
    result = svc.download_video(req.video_id, opts)
    info = result["info"]
    fp = result["filename"]
    return AudioInfo(
        video_id=info.get("id", req.video_id),
        title=info.get("title", ""),
        filename=os.path.basename(fp),
        filepath=fp,
        format=req.format.value,
        duration=info.get("duration"),
        filesize=os.path.getsize(fp) if os.path.exists(fp) else None,
    )


@router.get("/{video_id}/formats", summary="List audio-only formats",
            description="Returns only audio formats available for a video.")
async def get_audio_formats(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url)
    fmts = svc.get_formats(info)
    audio_only = [f for f in fmts if f.get("has_audio") and not f.get("has_video")]
    return {"video_id": info.get("id"), "title": info.get("title"), "audio_formats": audio_only}
