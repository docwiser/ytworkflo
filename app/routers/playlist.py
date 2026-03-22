from fastapi import APIRouter, Path, Query

from app.models.schemas import (
    PaginatedMeta,
    PlaylistInfo,
    PlaylistRequest,
    PlaylistVideosResponse,
    SearchResultItem,
    ThumbnailItem,
)
from app.services import ytdlp_service as svc

router = APIRouter()


@router.get(
    "/{playlist_id}",
    response_model=PlaylistVideosResponse,
    summary="Get playlist with videos",
    description="Fetch playlist metadata and all video entries.",
)
async def get_playlist(
    playlist_id: str = Path(..., description="Playlist ID or URL"),
    per_page: int = Query(50, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    url = svc.normalize_playlist(playlist_id)
    info = svc.extract_info(url, {"extract_flat": True, "playlistend": per_page})
    thumbs = [ThumbnailItem(**t) for t in svc.get_thumbnails(info)]
    playlist = PlaylistInfo(
        id=info.get("id", ""),
        title=info.get("title", ""),
        url=info.get("webpage_url") or url,
        description=info.get("description"),
        channel_id=info.get("channel_id") or info.get("uploader_id"),
        channel_name=info.get("uploader") or info.get("channel"),
        view_count=info.get("view_count"),
        modified_date=info.get("modified_date"),
        entry_count=info.get("playlist_count"),
        thumbnails=thumbs,
        availability=info.get("availability"),
    )
    entries = info.get("entries", []) or []
    videos = []
    for e in entries:
        if not e:
            continue
        thumb = None
        tn = e.get("thumbnails", [])
        if tn:
            thumb = tn[-1].get("url")
        videos.append(SearchResultItem(
            id=e.get("id", ""),
            type="video",
            title=e.get("title", ""),
            url=e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
            thumbnail=thumb or e.get("thumbnail"),
            duration=e.get("duration"),
            duration_string=e.get("duration_string"),
            view_count=e.get("view_count"),
            published_at=e.get("upload_date"),
            channel_name=e.get("uploader") or e.get("channel"),
            channel_id=e.get("channel_id"),
        ))
    return PlaylistVideosResponse(
        playlist=playlist,
        videos=videos,
        meta=PaginatedMeta(page=page, per_page=per_page, total=len(videos), has_more=len(videos) == per_page),
    )


@router.post("/info", response_model=PlaylistVideosResponse, summary="Get playlist info (POST)")
async def get_playlist_post(req: PlaylistRequest, per_page: int = Query(50, ge=1, le=100)):
    from app.routers.playlist import get_playlist
    return await get_playlist(req.playlist_id, per_page=per_page)


@router.get("/{playlist_id}/ids", summary="Get playlist video IDs only")
async def get_playlist_ids(playlist_id: str = Path(...)):
    url = svc.normalize_playlist(playlist_id)
    info = svc.extract_info(url, {"extract_flat": True})
    entries = info.get("entries", []) or []
    return {
        "playlist_id": info.get("id"),
        "title": info.get("title"),
        "video_ids": [e.get("id") for e in entries if e and e.get("id")],
        "total": len(entries),
    }
