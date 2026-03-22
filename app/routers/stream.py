from fastapi import APIRouter, Path, Query
from fastapi.responses import RedirectResponse

from app.models.schemas import (
    LiveStreamInfo,
    StreamInfo,
    StreamRequest,
    VideoQuality,
)
from app.services import ytdlp_service as svc

router = APIRouter()


@router.get(
    "/{video_id}",
    response_model=StreamInfo,
    summary="Get stream info",
    description="Returns direct streaming URL for a video. URL may expire.",
)
async def get_stream_info(
    video_id: str = Path(...),
    quality: VideoQuality = Query(VideoQuality.best),
    format_id: str = Query(None),
):
    url = svc.normalize_id(video_id)
    fmt = format_id or ("bestvideo+bestaudio/best" if quality == VideoQuality.best else
                        f"bestvideo[height<={quality.value.replace('p','')}]+bestaudio/best")
    info = svc.extract_info(url, {"format": fmt})
    fmts = info.get("formats", [])
    sel = fmts[-1] if fmts else {}

    return StreamInfo(
        video_id=info.get("id", video_id),
        title=info.get("title", ""),
        stream_url=sel.get("url") or info.get("url", ""),
        ext=sel.get("ext") or info.get("ext", ""),
        format_id=sel.get("format_id", "best"),
        resolution=sel.get("resolution"),
        fps=sel.get("fps"),
        tbr=sel.get("tbr"),
        is_live=bool(info.get("is_live")),
        manifest_url=info.get("manifest_url"),
        hls_url=info.get("hls_url") or info.get("manifest_url"),
        dash_url=info.get("dash_url") or info.get("mpd_url"),
    )


@router.get(
    "/{video_id}/redirect",
    summary="Redirect to stream URL",
    description="302 redirect directly to the video stream URL.",
)
async def redirect_to_stream(
    video_id: str = Path(...),
    quality: VideoQuality = Query(VideoQuality.best),
):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"format": "best"})
    fmts = info.get("formats", [])
    stream_url = fmts[-1].get("url") if fmts else info.get("url", "")
    return RedirectResponse(url=stream_url)


@router.get(
    "/{video_id}/hls",
    summary="Get HLS manifest URL",
    description="Returns HLS (.m3u8) manifest URL for adaptive streaming.",
)
async def get_hls_url(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url)
    hls = info.get("hls_url") or info.get("manifest_url")
    fmts = info.get("formats", [])
    if not hls:
        for f in fmts:
            if f.get("protocol") in ("m3u8", "m3u8_native") and f.get("url"):
                hls = f.get("url")
                break
    return {
        "video_id": info.get("id"),
        "title": info.get("title"),
        "hls_url": hls,
        "is_live": bool(info.get("is_live")),
    }


@router.get(
    "/{video_id}/dash",
    summary="Get DASH manifest URL",
    description="Returns DASH (.mpd) manifest URL.",
)
async def get_dash_url(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url)
    dash = info.get("dash_url") or info.get("mpd_url")
    fmts = info.get("formats", [])
    if not dash:
        for f in fmts:
            if f.get("protocol") in ("http_dash_segments",) and f.get("url"):
                dash = f.get("url")
                break
    return {
        "video_id": info.get("id"),
        "title": info.get("title"),
        "dash_url": dash,
        "is_live": bool(info.get("is_live")),
    }


@router.get(
    "/{video_id}/live",
    response_model=LiveStreamInfo,
    summary="Get live stream info",
    description="Check if a video/channel is live and return live stream URLs.",
)
async def get_live_stream(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"live_from_start": False})
    is_live = bool(info.get("is_live"))
    fmts = info.get("formats", [])
    hls = None
    if is_live:
        for f in fmts:
            if f.get("protocol") in ("m3u8", "m3u8_native"):
                hls = f.get("url")
                break
    return LiveStreamInfo(
        video_id=info.get("id", video_id),
        title=info.get("title", ""),
        is_live=is_live,
        stream_url=fmts[-1].get("url") if fmts and is_live else None,
        hls_url=hls,
        concurrent_viewers=info.get("concurrent_view_count"),
    )
