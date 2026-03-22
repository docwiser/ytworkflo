"""Transcript router"""
from fastapi import APIRouter, Path, Query
from app.models.schemas import (
    TranscriptListResponse, TranscriptRequest, TranscriptResponse,
    TranscriptSegment, Subtitle
)
from app.services import ytdlp_service as svc
from app.core.exceptions import ExtractionError
import re

router = APIRouter()


def _parse_vtt(content: str):
    segments = []
    blocks = re.split(r'\n\n+', content.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        time_line = next((l for l in lines if '-->' in l), None)
        if not time_line:
            continue
        times = re.findall(r'(\d{2}:\d{2}:\d{2}\.\d+|\d{2}:\d{2}\.\d+)', time_line)
        if len(times) < 2:
            continue
        def to_sec(t):
            parts = t.split(':')
            if len(parts) == 3:
                return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
            return float(parts[0])*60 + float(parts[1])
        start = to_sec(times[0])
        end = to_sec(times[1])
        text_lines = [l for l in lines if '-->' not in l and not l.strip().isdigit()]
        text = ' '.join(text_lines).strip()
        text = re.sub(r'<[^>]+>', '', text)
        if text:
            segments.append(TranscriptSegment(
                text=text, start=start, end=end, duration=round(end-start, 3)
            ))
    return segments


@router.get("/{video_id}", response_model=TranscriptResponse, summary="Get transcript",
            description="Fetches timestamped transcript/caption segments for a video.")
async def get_transcript(
    video_id: str = Path(...),
    language: str = Query("en", description="Language code"),
    auto_generated: bool = Query(True),
):
    url = svc.normalize_id(video_id)
    result = svc.get_subtitles_content(url, lang=language, fmt="vtt", auto=auto_generated)
    info = result.get("info") or {}
    content = result.get("content", "")
    segments = _parse_vtt(content) if content else []
    full_text = " ".join(s.text for s in segments)
    subs = info.get("subtitles", {})
    auto_caps = info.get("automatic_captions", {})
    is_auto = language not in subs and language in auto_caps
    return TranscriptResponse(
        video_id=info.get("id", video_id),
        title=info.get("title", ""),
        language=language,
        language_code=language,
        is_auto_generated=is_auto,
        segments=segments,
        full_text=full_text,
    )


@router.post("", response_model=TranscriptResponse, summary="Get transcript (POST)")
async def get_transcript_post(req: TranscriptRequest):
    from app.routers.transcript import get_transcript
    return await get_transcript(req.video_id, language=req.language, auto_generated=req.auto_generated)


@router.get("/{video_id}/languages", response_model=TranscriptListResponse,
            summary="List transcript languages")
async def list_transcript_languages(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    manual = info.get("subtitles", {})
    auto = info.get("automatic_captions", {})
    all_langs = []
    for lang_code, subs in manual.items():
        all_langs.append(Subtitle(
            language=lang_code, language_code=lang_code,
            url=(subs[0].get("url") if subs else None), is_auto_generated=False
        ))
    for lang_code, subs in auto.items():
        if lang_code not in manual:
            all_langs.append(Subtitle(
                language=lang_code, language_code=lang_code,
                url=(subs[0].get("url") if subs else None), is_auto_generated=True
            ))
    return TranscriptListResponse(
        video_id=info.get("id", video_id),
        available_languages=all_langs,
    )


@router.get("/{video_id}/full-text", summary="Get full transcript as plain text")
async def get_full_text(video_id: str = Path(...), language: str = Query("en"), auto_generated: bool = Query(True)):
    url = svc.normalize_id(video_id)
    result = svc.get_subtitles_content(url, lang=language, fmt="vtt", auto=auto_generated)
    info = result.get("info") or {}
    content = result.get("content", "")
    segments = _parse_vtt(content) if content else []
    return {
        "video_id": info.get("id", video_id),
        "title": info.get("title", ""),
        "language": language,
        "word_count": sum(len(s.text.split()) for s in segments),
        "segment_count": len(segments),
        "full_text": " ".join(s.text for s in segments),
    }
