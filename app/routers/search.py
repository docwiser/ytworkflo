from datetime import datetime
from typing import List

from fastapi import APIRouter, Query
from pydantic import Field

from app.core.exceptions import ExtractionError
from app.models.schemas import (
    PaginatedMeta,
    SearchFilter,
    SearchOrder,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.services import ytdlp_service as svc

router = APIRouter()


def _entry_to_result(e: dict) -> SearchResultItem:
    etype = e.get("_type", "video")
    vid = e.get("id", "")
    url = e.get("url") or e.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
    thumb = None
    thumbs = e.get("thumbnails", [])
    if thumbs:
        thumb = thumbs[-1].get("url")
    elif e.get("thumbnail"):
        thumb = e.get("thumbnail")
    return SearchResultItem(
        id=vid,
        type=etype,
        title=e.get("title") or "",
        url=url,
        thumbnail=thumb,
        description=e.get("description"),
        published_at=e.get("upload_date"),
        channel_name=e.get("uploader") or e.get("channel"),
        channel_id=e.get("channel_id") or e.get("uploader_id"),
        view_count=e.get("view_count"),
        duration=e.get("duration"),
        duration_string=e.get("duration_string"),
        is_live=bool(e.get("is_live")),
    )


@router.post(
    "",
    response_model=SearchResponse,
    summary="Search YouTube",
    description="Full-text YouTube search with filters, ordering, and pagination.",
)
async def search(req: SearchRequest):
    results_raw = svc.search_videos(req.query, limit=req.per_page)
    items = [_entry_to_result(e) for e in results_raw if e]
    return SearchResponse(
        query=req.query,
        results=items,
        meta=PaginatedMeta(
            page=req.page,
            per_page=req.per_page,
            total=len(items),
            has_more=len(items) == req.per_page,
        ),
    )


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search YouTube (GET)",
    description="GET version of search — pass query as query param.",
)
async def search_get(
    q: str = Query(..., description="Search query"),
    order: SearchOrder = Query(SearchOrder.relevance),
    filter: SearchFilter = Query(None),
    per_page: int = Query(20, ge=1, le=50),
    page: int = Query(1, ge=1),
):
    results_raw = svc.search_videos(q, limit=per_page)
    items = [_entry_to_result(e) for e in results_raw if e]
    return SearchResponse(
        query=q,
        results=items,
        meta=PaginatedMeta(
            page=page,
            per_page=per_page,
            total=len(items),
            has_more=len(items) == per_page,
        ),
    )


@router.get(
    "/suggest",
    response_model=List[str],
    summary="Search suggestions",
    description="Returns autocomplete suggestions for a query using YouTube's suggestion API.",
)
async def search_suggestions(
    q: str = Query(..., description="Partial query to complete"),
    lang: str = Query("en", description="Language code"),
):
    import urllib.parse
    import urllib.request
    import json

    encoded = urllib.parse.quote(q)
    url = f"https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={encoded}&hl={lang}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [item[0] for item in data[1]]
    except Exception:
        return []


@router.get(
    "/related/{video_id}",
    response_model=SearchResponse,
    summary="Related videos",
    description="Fetch videos related to a given video by searching its title and tags.",
)
async def related_videos(
    video_id: str,
    limit: int = Query(10, ge=1, le=30),
):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"extract_flat": True})
    title = info.get("title", "")
    tags = info.get("tags", [])[:3]
    query = title + " " + " ".join(tags)
    results_raw = svc.search_videos(query[:100], limit=limit)
    items = [_entry_to_result(e) for e in results_raw if e.get("id") != video_id]
    return SearchResponse(
        query=query,
        results=items,
        meta=PaginatedMeta(page=1, per_page=limit, total=len(items), has_more=False),
    )
