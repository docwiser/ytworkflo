"""Comments router"""
from fastapi import APIRouter, Path, Query
from app.models.schemas import CommentItem, CommentsRequest, CommentsResponse, PaginatedMeta
from app.services import ytdlp_service as svc

router = APIRouter()


@router.get("/{video_id}", response_model=CommentsResponse, summary="Get video comments",
            description="Fetches top or recent comments for a video.")
async def get_comments(
    video_id: str = Path(...),
    sort_by: str = Query("top", description="'top' or 'new'"),
    limit: int = Query(20, ge=1, le=200),
):
    url = svc.normalize_id(video_id)
    raw_comments = svc.get_comments(url, limit=limit, sort_by=sort_by)
    info_basic = svc.extract_info(url, {"skip_download": True})

    items = []
    for c in raw_comments[:limit]:
        items.append(CommentItem(
            id=c.get("id", ""),
            author=c.get("author", ""),
            author_id=c.get("author_id"),
            text=c.get("text", ""),
            timestamp=c.get("timestamp"),
            like_count=c.get("like_count"),
            reply_count=c.get("reply_count"),
            is_pinned=bool(c.get("is_pinned")),
            is_favorited=bool(c.get("is_favorited")),
            parent_id=c.get("parent"),
        ))
    top_level = [c for c in items if not c.parent_id]
    return CommentsResponse(
        video_id=info_basic.get("id", video_id),
        title=info_basic.get("title", ""),
        comment_count=info_basic.get("comment_count"),
        comments=items,
        meta=PaginatedMeta(page=1, per_page=limit, total=len(items), has_more=len(items) == limit),
    )


@router.post("", response_model=CommentsResponse, summary="Get comments (POST)")
async def get_comments_post(req: CommentsRequest):
    from app.routers.comments import get_comments
    return await get_comments(req.video_id, sort_by=req.sort_by, limit=req.limit)


@router.get("/{video_id}/replies/{comment_id}", summary="Get comment replies")
async def get_comment_replies(video_id: str = Path(...), comment_id: str = Path(...), limit: int = Query(10)):
    url = svc.normalize_id(video_id)
    all_comments = svc.get_comments(url, limit=200)
    replies = [c for c in all_comments if c.get("parent") == comment_id]
    return {
        "video_id": video_id,
        "comment_id": comment_id,
        "replies": replies[:limit],
        "total": len(replies),
    }


@router.get("/{video_id}/pinned", summary="Get pinned comment")
async def get_pinned_comment(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    comments = svc.get_comments(url, limit=50)
    pinned = next((c for c in comments if c.get("is_pinned")), None)
    return {"video_id": video_id, "pinned_comment": pinned}
