"""Subtitles router"""
import os
import re
from fastapi import APIRouter, Path, Query
from fastapi.responses import FileResponse, PlainTextResponse
from app.models.schemas import (
    SubtitleContentResponse, SubtitleDownloadRequest, SubtitleDownloadResponse,
    SubtitleFormat, TranscriptSegment,
)
from app.services import ytdlp_service as svc
from app.core.config import settings

router = APIRouter()


def _vtt_to_srt(vtt: str) -> str:
    """Convert WebVTT content to SRT format."""
    lines = vtt.splitlines()
    srt_lines = []
    counter = 1
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '-->' in line:
            # Convert VTT timestamp to SRT (. -> ,)
            ts = line.replace('.', ',')
            # Remove positioning tags
            ts = re.sub(r' (align|position|line|size):[^\s]+', '', ts)
            srt_lines.append(str(counter))
            srt_lines.append(ts)
            counter += 1
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip():
                text = re.sub(r'<[^>]+>', '', lines[i])
                text_lines.append(text)
                i += 1
            srt_lines.append('\n'.join(text_lines))
            srt_lines.append('')
        else:
            i += 1
    return '\n'.join(srt_lines)


def _parse_vtt_segments(content: str):
    segments = []
    blocks = re.split(r'\n\n+', content.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        time_line = next((l for l in lines if '-->' in l), None)
        if not time_line:
            continue
        times = re.findall(r'(\d{2}:\d{2}:\d{2}[.,]\d+|\d{2}:\d{2}[.,]\d+)', time_line)
        if len(times) < 2:
            continue
        def to_sec(t):
            t = t.replace(',', '.')
            parts = t.split(':')
            if len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            return float(parts[0]) * 60 + float(parts[1])
        start = to_sec(times[0])
        end = to_sec(times[1])
        text_lines = [l for l in lines if '-->' not in l and not l.strip().isdigit()
                      and not l.strip().startswith('WEBVTT')]
        text = ' '.join(text_lines).strip()
        text = re.sub(r'<[^>]+>', '', text).strip()
        if text:
            segments.append(TranscriptSegment(
                text=text, start=start, end=end, duration=round(end - start, 3)
            ))
    return segments


@router.get(
    "/{video_id}",
    response_model=SubtitleContentResponse,
    summary="Get subtitle content",
    description="Fetch subtitle/caption content for a video in the requested format.",
)
async def get_subtitles(
    video_id: str = Path(...),
    language: str = Query("en", description="Language code, e.g. 'en', 'hi', 'es'"),
    format: SubtitleFormat = Query(SubtitleFormat.srt),
    auto_generated: bool = Query(True, description="Allow auto-generated captions"),
):
    url = svc.normalize_id(video_id)
    result = svc.get_subtitles_content(url, lang=language, fmt="vtt", auto=auto_generated)
    info = result.get("info") or {}
    vtt_content = result.get("content", "")

    # Convert to requested format
    if format == SubtitleFormat.srt:
        content = _vtt_to_srt(vtt_content)
    elif format == SubtitleFormat.vtt:
        content = vtt_content
    else:
        content = vtt_content  # return VTT for other formats (full conversion requires ffmpeg)

    segments = _parse_vtt_segments(vtt_content)

    return SubtitleContentResponse(
        video_id=info.get("id", video_id),
        language=language,
        format=format.value,
        content=content,
        segments=segments,
    )


@router.post(
    "/download",
    response_model=SubtitleDownloadResponse,
    summary="Download subtitle file",
    description="Download subtitle file to server and return file info.",
)
async def download_subtitle(req: SubtitleDownloadRequest):
    url = svc.normalize_id(req.video_id)
    result = svc.get_subtitles_content(url, lang=req.language, fmt="vtt", auto=req.auto_generated)
    info = result.get("info") or {}
    vtt_content = result.get("content", "")

    # Convert if needed
    if req.format == SubtitleFormat.srt:
        final_content = _vtt_to_srt(vtt_content)
        ext = "srt"
    else:
        final_content = vtt_content
        ext = "vtt"

    os.makedirs(settings.SUBTITLE_DIR, exist_ok=True)
    vid_id = info.get("id", req.video_id)
    filename = f"{vid_id}_{req.language}.{ext}"
    filepath = os.path.join(settings.SUBTITLE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_content)

    return SubtitleDownloadResponse(
        video_id=vid_id,
        language=req.language,
        format=ext,
        filename=filename,
        filepath=filepath,
        content_preview=final_content[:500] if final_content else None,
    )


@router.get(
    "/{video_id}/file",
    summary="Serve subtitle as downloadable file",
    description="Returns subtitle as a raw file download.",
)
async def serve_subtitle_file(
    video_id: str = Path(...),
    language: str = Query("en"),
    format: SubtitleFormat = Query(SubtitleFormat.srt),
    auto_generated: bool = Query(True),
):
    url = svc.normalize_id(video_id)
    result = svc.get_subtitles_content(url, lang=language, fmt="vtt", auto=auto_generated)
    vtt_content = result.get("content", "")

    if format == SubtitleFormat.srt:
        content = _vtt_to_srt(vtt_content)
        ext = "srt"
        media_type = "text/plain"
    else:
        content = vtt_content
        ext = "vtt"
        media_type = "text/vtt"

    os.makedirs(settings.SUBTITLE_DIR, exist_ok=True)
    filename = f"{video_id}_{language}.{ext}"
    filepath = os.path.join(settings.SUBTITLE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return FileResponse(filepath, media_type=media_type, filename=filename)


@router.get(
    "/{video_id}/available",
    summary="List available subtitles",
    description="Returns all available subtitle languages for a video.",
)
async def list_available_subtitles(video_id: str = Path(...)):
    url = svc.normalize_id(video_id)
    info = svc.extract_info(url, {"skip_download": True})
    manual = info.get("subtitles", {})
    auto = info.get("automatic_captions", {})

    manual_list = [
        {
            "language_code": lang,
            "is_auto_generated": False,
            "formats": [s.get("ext") for s in subs if s.get("ext")],
        }
        for lang, subs in manual.items()
    ]
    auto_list = [
        {
            "language_code": lang,
            "is_auto_generated": True,
            "formats": [s.get("ext") for s in subs if s.get("ext")],
        }
        for lang, subs in auto.items()
        if lang not in manual
    ]

    return {
        "video_id": info.get("id", video_id),
        "title": info.get("title", ""),
        "manual_subtitles": manual_list,
        "auto_generated": auto_list,
        "all_language_codes": sorted(set(list(manual.keys()) + list(auto.keys()))),
    }
