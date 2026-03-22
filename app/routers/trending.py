"""Trending router"""
from datetime import datetime
from fastapi import APIRouter, Query
from app.models.schemas import SearchResultItem, TrendingCategory, TrendingRequest, TrendingResponse
from app.services import ytdlp_service as svc

router = APIRouter()

CATEGORY_NAMES = {
    "0": "Default", "10": "Music", "20": "Gaming",
    "30": "Movies", "25": "News", "17": "Sports", "28": "Science & Tech",
}


@router.get("", response_model=TrendingResponse, summary="Get trending videos",
            description="Fetch currently trending YouTube videos by region and category.")
async def get_trending(
    region: str = Query("US", description="ISO 3166-1 alpha-2 region code, e.g. 'US', 'IN', 'GB'"),
    category: TrendingCategory = Query(TrendingCategory.default),
    limit: int = Query(20, ge=1, le=50),
):
    url = f"https://www.youtube.com/feed/trending?gl={region}&bp={category.value}"
    # yt-dlp can scrape trending via the trending URL
    try:
        info = svc.extract_info(url, {"extract_flat": True, "playlistend": limit})
        entries = info.get("entries", []) or []
    except Exception:
        # Fallback: search for "trending" in the region
        entries = svc.search_videos(f"trending {CATEGORY_NAMES.get(category.value, '')}", limit=limit)

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
            url=e.get("url") or e.get("webpage_url") or f"https://www.youtube.com/watch?v={e.get('id')}",
            thumbnail=thumb or e.get("thumbnail"),
            duration=e.get("duration"),
            duration_string=e.get("duration_string"),
            view_count=e.get("view_count"),
            published_at=e.get("upload_date"),
            channel_name=e.get("uploader") or e.get("channel"),
            channel_id=e.get("channel_id"),
            is_live=bool(e.get("is_live")),
        ))

    return TrendingResponse(
        region=region,
        category=CATEGORY_NAMES.get(category.value, "Default"),
        fetched_at=datetime.utcnow().isoformat() + "Z",
        videos=videos[:limit],
    )


@router.get("/regions", summary="List supported trending regions")
async def list_regions():
    return {
        "regions": [
            {"code": "US", "name": "United States"},
            {"code": "IN", "name": "India"},
            {"code": "GB", "name": "United Kingdom"},
            {"code": "CA", "name": "Canada"},
            {"code": "AU", "name": "Australia"},
            {"code": "DE", "name": "Germany"},
            {"code": "FR", "name": "France"},
            {"code": "JP", "name": "Japan"},
            {"code": "KR", "name": "South Korea"},
            {"code": "BR", "name": "Brazil"},
            {"code": "MX", "name": "Mexico"},
            {"code": "RU", "name": "Russia"},
            {"code": "NG", "name": "Nigeria"},
            {"code": "ZA", "name": "South Africa"},
            {"code": "EG", "name": "Egypt"},
            {"code": "SA", "name": "Saudi Arabia"},
            {"code": "IT", "name": "Italy"},
            {"code": "ES", "name": "Spain"},
            {"code": "NL", "name": "Netherlands"},
            {"code": "PL", "name": "Poland"},
        ]
    }


@router.get("/categories", summary="List trending categories")
async def list_categories():
    return {
        "categories": [
            {"id": k, "name": v}
            for k, v in CATEGORY_NAMES.items()
        ]
    }
