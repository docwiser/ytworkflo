"""Channel router"""
from fastapi import APIRouter, Path, Query

from app.models.schemas import (
    ChannelInfo,
    ChannelRequest,
    ChannelVideosResponse,
    PaginatedMeta,
    SearchResultItem,
    ThumbnailItem,
)
from app.services import ytdlp_service as svc

router = APIRouter()


@router.get(
    "/{channel_id}",
    response_model=ChannelInfo,
    summary="Get channel info",
    description="Fetch channel metadata: subscriber count, description, thumbnails, etc.",
)
async def get_channel(channel_id: str = Path(..., description="Channel ID, @handle, or URL")):
    url = svc.normalize_channel(channel_id)
    info = svc.extract_info(url, {"extract_flat": True, "playlistend": 1})
    thumbs = [ThumbnailItem(**t) for t in svc.get_thumbnails(info)]
    return ChannelInfo(
        id=info.get("channel_id") or info.get("id", ""),
        name=info.get("uploader") or info.get("channel") or info.get("title", ""),
        url=info.get("webpage_url") or url,
        handle=info.get("uploader_id"),
        description=info.get("description"),
        subscriber_count=info.get("channel_follower_count"),
        video_count=info.get("playlist_count"),
        view_count=info.get("view_count"),
        country=info.get("uploader_url"),
        thumbnails=thumbs,
        tags=info.get("tags") or [],
    )


@router.get(
    "/{channel_id}/videos",
    response_model=ChannelVideosResponse,
    summary="Get channel videos",
    description="List videos from a channel with pagination.",
)
async def get_channel_videos(
    channel_id: str = Path(...),
    per_page: int = Query(20, ge=1, le=50),
    page: int = Query(1, ge=1),
):
    url = svc.normalize_channel(channel_id) + "/videos"
    info = svc.extract_info(url, {"extract_flat": True, "playlistend": per_page})
    entries = info.get("entries", []) or []
    videos = []
    for e in entries:
        if not e:
            continue
        thumb = None
        thumbs = e.get("thumbnails", [])
        if thumbs:
            thumb = thumbs[-1].get("url")
        videos.append(SearchResultItem(
            id=e.get("id", ""),
            type="video",
            title=e.get("title", ""),
            url=e.get("url") or e.get("webpage_url") or f"https://www.youtube.com/watch?v={e.get('id')}",
            thumbnail=thumb or e.get("thumbnail"),
            duration=e.get("duration"),
            duration_string=e.get("duration_string"),
            view_count=e.get("view_count"),
            published_at=e.get("upload_date"),
            channel_name=info.get("uploader") or info.get("channel"),
            channel_id=info.get("channel_id"),
        ))
    return ChannelVideosResponse(
        channel_id=info.get("channel_id") or channel_id,
        channel_name=info.get("uploader") or info.get("channel") or channel_id,
        videos=videos,
        meta=PaginatedMeta(page=page, per_page=per_page, total=len(videos), has_more=len(videos) == per_page),
    )


@router.get("/{channel_id}/playlists", summary="Get channel playlists")
async def get_channel_playlists(channel_id: str = Path(...), limit: int = Query(20, ge=1, le=50)):
    url = svc.normalize_channel(channel_id) + "/playlists"
    info = svc.extract_info(url, {"extract_flat": True, "playlistend": limit})
    entries = info.get("entries", []) or []
    return {
        "channel_id": info.get("channel_id") or channel_id,
        "channel_name": info.get("uploader") or info.get("channel"),
        "playlists": [
            {
                "id": e.get("id"),
                "title": e.get("title"),
                "url": e.get("url"),
                "video_count": e.get("playlist_count"),
                "thumbnail": (e.get("thumbnails") or [{}])[-1].get("url"),
            }
            for e in entries if e
        ],
    }


@router.get("/{channel_id}/about", summary="Channel about/description")
async def get_channel_about(channel_id: str = Path(...)):
    url = svc.normalize_channel(channel_id)
    info = svc.extract_info(url, {"extract_flat": True, "playlistend": 0})
    return {
        "id": info.get("channel_id") or info.get("id"),
        "name": info.get("uploader") or info.get("channel") or info.get("title"),
        "description": info.get("description"),
        "country": info.get("uploader_url"),
        "tags": info.get("tags") or [],
        "subscriber_count": info.get("channel_follower_count"),
        "video_count": info.get("playlist_count"),
    }
