"""Formats router"""
from fastapi import APIRouter, Path, Query
from app.models.schemas import FormatFilterRequest, FormatsResponse, VideoFormat
from app.services import ytdlp_service as svc

router = APIRouter()


@router.get("/{video_id}", response_model=FormatsResponse, summary="List all formats",
            description="Returns all available download formats for a video.")
async def get_formats(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url)
    fmts = [VideoFormat(**f) for f in svc.get_formats(info)]
    best_video = next((f for f in reversed(fmts) if f.has_video and not f.has_audio), None)
    best_audio = next((f for f in reversed(fmts) if f.has_audio and not f.has_video), None)
    best_combined = next((f for f in reversed(fmts) if f.has_video and f.has_audio), None)
    return FormatsResponse(
        video_id=info.get("id", video_id),
        title=info.get("title", ""),
        formats=fmts,
        best_video=best_video,
        best_audio=best_audio,
        best_combined=best_combined,
    )


@router.post("/filter", response_model=list, summary="Filter formats",
             description="Get formats matching specific criteria.")
async def filter_formats(req: FormatFilterRequest):
    url = svc.normalize_id(req.video_id)
    info = svc.extract_info(url)
    fmts = svc.get_formats(info)
    filtered = fmts
    if req.ext:
        filtered = [f for f in filtered if f.get("ext") == req.ext]
    if req.has_video is not None:
        filtered = [f for f in filtered if f.get("has_video") == req.has_video]
    if req.has_audio is not None:
        filtered = [f for f in filtered if f.get("has_audio") == req.has_audio]
    if req.min_height:
        def h(f):
            r = f.get("resolution") or ""
            return int(r.split("x")[-1]) if "x" in r else 0
        filtered = [f for f in filtered if h(f) >= req.min_height]
    if req.max_height:
        def h2(f):
            r = f.get("resolution") or ""
            return int(r.split("x")[-1]) if "x" in r else 9999
        filtered = [f for f in filtered if h2(f) <= req.max_height]
    if req.vcodec:
        filtered = [f for f in filtered if req.vcodec.lower() in (f.get("vcodec") or "").lower()]
    if req.acodec:
        filtered = [f for f in filtered if req.acodec.lower() in (f.get("acodec") or "").lower()]
    return filtered


@router.get("/{video_id}/video-only", summary="Video-only formats")
async def video_only_formats(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url)
    fmts = svc.get_formats(info)
    return [f for f in fmts if f.get("has_video") and not f.get("has_audio")]


@router.get("/{video_id}/by-ext/{ext}", summary="Formats by file extension")
async def formats_by_ext(video_id: str = Path(...), ext: str = Path(..., description="e.g. mp4, webm")):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url)
    fmts = svc.get_formats(info)
    return [f for f in fmts if f.get("ext") == ext]
