"""Analytics router"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Path
from app.models.schemas import ChannelAnalytics, EngagementMetrics, Heatmap, VideoAnalytics
from app.services import ytdlp_service as svc

router = APIRouter()


def _engagement(info: dict) -> EngagementMetrics:
    views = info.get("view_count") or 0
    likes = info.get("like_count") or 0
    comments = info.get("comment_count") or 0
    like_ratio = round(likes / views, 6) if views else None
    engagement_rate = round((likes + comments) / views * 100, 4) if views else None
    upload = info.get("upload_date")
    age_days = None
    vpd = None
    if upload:
        try:
            uploaded = datetime.strptime(upload, "%Y%m%d")
            age_days = (datetime.utcnow() - uploaded).days or 1
            vpd = round(views / age_days, 2)
        except Exception:
            pass
    reach = None
    if views:
        if views >= 1_000_000:
            reach = f"{views/1_000_000:.1f}M"
        elif views >= 1_000:
            reach = f"{views/1_000:.1f}K"
        else:
            reach = str(views)
    return EngagementMetrics(
        view_count=views or None,
        like_count=likes or None,
        comment_count=comments or None,
        like_ratio=like_ratio,
        engagement_rate=engagement_rate,
        views_per_day=vpd,
        estimated_reach=reach,
    )


@router.get("/{video_id}", response_model=VideoAnalytics, summary="Video analytics",
            description="Engagement metrics, heatmap, performance score, and top moments.")
async def get_video_analytics(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    eng = _engagement(info)
    hm_raw = info.get("heatmap") or []
    hm = [Heatmap(start_time=h.get("start_time",0), end_time=h.get("end_time",0), value=h.get("value",0)) for h in hm_raw]
    top_moments = sorted(hm_raw, key=lambda h: h.get("value", 0), reverse=True)[:5] if hm_raw else []

    # Simple performance score 0-100
    score = None
    if eng.engagement_rate is not None:
        score = min(100.0, round(eng.engagement_rate * 20, 1))

    upload = info.get("upload_date")
    age_days = None
    if upload:
        try:
            age_days = (datetime.utcnow() - datetime.strptime(upload, "%Y%m%d")).days
        except Exception:
            pass

    return VideoAnalytics(
        video_id=info.get("id", video_id),
        title=info.get("title", ""),
        upload_date=upload,
        duration=info.get("duration"),
        age_days=age_days,
        engagement=eng,
        heatmap=hm,
        top_moments=top_moments,
        performance_score=score,
        tags=info.get("tags") or [],
        categories=info.get("categories") or [],
    )


@router.get("/channel/{channel_id}", response_model=ChannelAnalytics, summary="Channel analytics")
async def get_channel_analytics(channel_id: str = Path(...)):
    url = svc.normalize_channel(channel_id) + "/videos"
    info = svc.extract_info(url, {"extract_flat": True, "playlistend": 5})
    entries = info.get("entries", []) or []
    total_views = sum(e.get("view_count") or 0 for e in entries if e)
    count = info.get("playlist_count") or len(entries)
    avg = round(total_views / len(entries), 0) if entries else None
    sub = info.get("channel_follower_count")
    estimated_monthly = round(avg * 30 / max(1, count), 0) if avg and count else None
    return ChannelAnalytics(
        channel_id=info.get("channel_id") or channel_id,
        channel_name=info.get("uploader") or info.get("channel") or channel_id,
        subscriber_count=sub,
        total_views=total_views or None,
        video_count=count or None,
        avg_views_per_video=avg,
        estimated_monthly_views=estimated_monthly,
    )


@router.get("/{video_id}/compare", summary="Compare video against channel average")
async def compare_video_to_channel(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    vid_views = info.get("view_count") or 0
    channel_id = info.get("channel_id")
    result = {
        "video_id": info.get("id"),
        "title": info.get("title"),
        "view_count": vid_views,
        "channel_id": channel_id,
    }
    if channel_id:
        try:
            ch_url = svc.normalize_channel(channel_id) + "/videos"
            ch_info = svc.extract_info(ch_url, {"extract_flat": True, "playlistend": 10})
            entries = ch_info.get("entries", []) or []
            views = [e.get("view_count") or 0 for e in entries if e]
            avg = round(sum(views) / len(views), 0) if views else 0
            result["channel_avg_views"] = avg
            result["vs_average"] = round((vid_views - avg) / avg * 100, 2) if avg else None
            result["percentile"] = round(sum(1 for v in views if v < vid_views) / len(views) * 100, 1) if views else None
        except Exception:
            pass
    return result
