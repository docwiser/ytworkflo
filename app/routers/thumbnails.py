"""Thumbnails router"""
import os
import urllib.request

from fastapi import APIRouter, Path, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.schemas import ThumbnailItem, ThumbnailsResponse
from app.services import ytdlp_service as svc

router = APIRouter()

STANDARD_THUMBS = {
    "maxres": "maxresdefault",
    "hq": "hqdefault",
    "mq": "mqdefault",
    "sd": "sddefault",
    "default": "default",
    "1": "1", "2": "2", "3": "3",
}


@router.get("/{video_id}", response_model=ThumbnailsResponse, summary="Get all thumbnails",
            description="Returns all thumbnail URLs for a video at every available resolution.")
async def get_thumbnails(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    thumbs = [ThumbnailItem(**t) for t in svc.get_thumbnails(info)]
    best = max(thumbs, key=lambda t: (t.width or 0) * (t.height or 0), default=None) if thumbs else None
    return ThumbnailsResponse(
        video_id=info.get("id", video_id),
        title=info.get("title", ""),
        thumbnails=thumbs,
        best=best,
    )


@router.get("/{video_id}/best", summary="Get best quality thumbnail URL")
async def get_best_thumbnail(video_id: str = Path(...)):
    clean_id = video_id.split("v=")[-1].split("&")[0] if "v=" in video_id else video_id
    url = f"https://i.ytimg.com/vi/{clean_id}/maxresdefault.jpg"
    return {"video_id": clean_id, "resolution": "maxres", "url": url,
            "width": 1280, "height": 720}


@router.get("/{video_id}/all-resolutions", summary="Get standard YouTube thumbnail URLs")
async def get_all_standard_thumbnails(video_id: str = Path(...)):
    clean_id = video_id.split("v=")[-1].split("&")[0] if "v=" in video_id else video_id
    return {
        "video_id": clean_id,
        "thumbnails": {
            name: {
                "url": f"https://i.ytimg.com/vi/{clean_id}/{key}.jpg",
                "resolution": name,
            }
            for name, key in STANDARD_THUMBS.items()
        },
    }


@router.get("/{video_id}/download", summary="Download thumbnail to server")
async def download_thumbnail(
    video_id: str = Path(...),
    resolution: str = Query("maxres", description="'maxres','hq','mq','default'"),
):
    os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)
    clean_id = video_id.split("v=")[-1].split("&")[0] if "v=" in video_id else video_id
    key = STANDARD_THUMBS.get(resolution, "maxresdefault")
    img_url = f"https://i.ytimg.com/vi/{clean_id}/{key}.jpg"
    filepath = os.path.join(settings.THUMBNAIL_DIR, f"{clean_id}_{resolution}.jpg")
    urllib.request.urlretrieve(img_url, filepath)
    return FileResponse(filepath, media_type="image/jpeg", filename=f"{clean_id}_{resolution}.jpg")
