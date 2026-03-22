from fastapi import APIRouter, Path, Query

from app.models.schemas import (
    Chapter,
    Heatmap,
    ThumbnailItem,
    VideoFormat,
    VideoInfo,
    VideoRequest,
)
from app.services import ytdlp_service as svc

router = APIRouter()


def _build_video_info(info: dict, include_formats: bool = True) -> VideoInfo:
    thumbs = [ThumbnailItem(**t) for t in svc.get_thumbnails(info)]
    chapters = [
        Chapter(
            title=c.get("title", ""),
            start_time=c.get("start_time", 0),
            end_time=c.get("end_time"),
        )
        for c in (info.get("chapters") or [])
    ]
    heatmap = [
        Heatmap(
            start_time=h.get("start_time", 0),
            end_time=h.get("end_time", 0),
            value=h.get("value", 0),
        )
        for h in (info.get("heatmap") or [])
    ]
    formats = [VideoFormat(**f) for f in svc.get_formats(info)] if include_formats else []
    return VideoInfo(
        id=info.get("id", ""),
        title=info.get("title", ""),
        url=info.get("webpage_url") or svc.normalize_id(info.get("id", "")),
        description=info.get("description"),
        duration=info.get("duration"),
        duration_string=info.get("duration_string"),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        comment_count=info.get("comment_count"),
        channel_id=info.get("channel_id"),
        channel_name=info.get("uploader") or info.get("channel"),
        channel_url=info.get("channel_url") or info.get("uploader_url"),
        channel_follower_count=info.get("channel_follower_count"),
        upload_date=info.get("upload_date"),
        timestamp=info.get("timestamp"),
        is_live=bool(info.get("is_live")),
        was_live=bool(info.get("was_live")),
        categories=info.get("categories") or [],
        tags=info.get("tags") or [],
        age_limit=info.get("age_limit") or 0,
        language=info.get("language"),
        thumbnails=thumbs,
        chapters=chapters,
        subtitles=info.get("subtitles") or {},
        automatic_captions=info.get("automatic_captions") or {},
        heatmap=heatmap,
        formats=formats,
        webpage_url=info.get("webpage_url"),
        extractor=info.get("extractor", "youtube"),
        availability=info.get("availability"),
    )


@router.get(
    "/{video_id}",
    response_model=VideoInfo,
    summary="Get video info",
    description="Full metadata for a YouTube video including formats, thumbnails, chapters, subtitles.",
)
async def get_video(
    video_id: str = Path(..., description="Video ID or full URL"),
    include_formats: bool = Query(True, description="Include format list"),
):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url)
    return _build_video_info(info, include_formats=include_formats)


@router.post(
    "/info",
    response_model=VideoInfo,
    summary="Get video info (POST)",
    description="POST-based video info fetch, useful when passing full URLs.",
)
async def get_video_post(req: VideoRequest):
    url = svc.normalize_id(req.video_id)
    info = svc.extract_info(url)
    return _build_video_info(info)


@router.get(
    "/{video_id}/metadata",
    summary="Lightweight video metadata",
    description="Returns only core metadata without format list — faster response.",
)
async def get_video_metadata(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("uploader") or info.get("channel"),
        "channel_id": info.get("channel_id"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "duration_string": info.get("duration_string"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "tags": info.get("tags", []),
        "categories": info.get("categories", []),
        "is_live": info.get("is_live"),
        "age_limit": info.get("age_limit", 0),
        "availability": info.get("availability"),
        "language": info.get("language"),
    }


@router.get(
    "/{video_id}/chapters",
    response_model=list,
    summary="Get video chapters",
    description="Returns chapter markers with timestamps.",
)
async def get_chapters(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    return info.get("chapters") or []


@router.get(
    "/{video_id}/heatmap",
    response_model=list,
    summary="Get engagement heatmap",
    description="Returns heatmap data showing most replayed moments.",
)
async def get_heatmap(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    return info.get("heatmap") or []


@router.get(
    "/{video_id}/tags",
    response_model=list,
    summary="Get video tags",
)
async def get_tags(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    return info.get("tags") or []


@router.get(
    "/{video_id}/available-subtitles",
    summary="List available subtitle languages",
    description="Returns all subtitle languages (manual + auto-generated) for a video.",
)
async def get_available_subtitles(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    manual = {
        lang: [{"url": s.get("url"), "ext": s.get("ext")} for s in subs]
        for lang, subs in (info.get("subtitles") or {}).items()
    }
    auto = {
        lang: [{"url": s.get("url"), "ext": s.get("ext")} for s in subs]
        for lang, subs in (info.get("automatic_captions") or {}).items()
    }
    return {
        "video_id": info.get("id"),
        "manual_subtitles": manual,
        "automatic_captions": auto,
        "manual_languages": list(manual.keys()),
        "auto_languages": list(auto.keys()),
    }


@router.get(
    "/{video_id}/is-live",
    summary="Check if video is a live stream",
)
async def check_live(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    return {
        "video_id": info.get("id"),
        "title": info.get("title"),
        "is_live": bool(info.get("is_live")),
        "was_live": bool(info.get("was_live")),
        "concurrent_view_count": info.get("concurrent_view_count"),
    }
