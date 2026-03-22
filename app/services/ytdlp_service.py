"""
ytworkflo — yt-dlp Service
Central wrapper around yt-dlp for all extraction tasks.
"""

import os
import re
import uuid
from typing import Any, Dict, List, Optional

import yt_dlp

from app.core.config import settings
from app.core.exceptions import ExtractionError, VideoNotFoundError


def _make_ydl_opts(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": settings.YTDLP_SOCKET_TIMEOUT,
        "retries": settings.YTDLP_RETRIES,
        "ignoreerrors": False,
    }
    if extra:
        base.update(extra)
    return base


def normalize_id(video_id: str) -> str:
    """Accept full URLs or bare IDs."""
    if video_id.startswith("http"):
        return video_id
    return f"https://www.youtube.com/watch?v={video_id}"


def normalize_channel(channel_id: str) -> str:
    if channel_id.startswith("http"):
        return channel_id
    if channel_id.startswith("@"):
        return f"https://www.youtube.com/{channel_id}"
    if channel_id.startswith("UC"):
        return f"https://www.youtube.com/channel/{channel_id}"
    return f"https://www.youtube.com/@{channel_id}"


def normalize_playlist(playlist_id: str) -> str:
    if playlist_id.startswith("http"):
        return playlist_id
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def extract_info(url: str, opts: Optional[Dict[str, Any]] = None, process: bool = True) -> Dict[str, Any]:
    ydl_opts = _make_ydl_opts(opts)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False, process=process)
            if info is None:
                raise VideoNotFoundError(url)
            return info
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "not available" in msg or "removed" in msg or "private" in msg:
            raise VideoNotFoundError(url)
        raise ExtractionError(msg)
    except Exception as e:
        raise ExtractionError(str(e))


def get_thumbnails(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    thumbs = info.get("thumbnails", [])
    return [
        {
            "url": t.get("url", ""),
            "width": t.get("width"),
            "height": t.get("height"),
            "resolution": t.get("resolution") or (
                f"{t['width']}x{t['height']}" if t.get("width") and t.get("height") else None
            ),
        }
        for t in thumbs
        if t.get("url")
    ]


def get_formats(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    fmts = info.get("formats", [])
    result = []
    for f in fmts:
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        result.append({
            "format_id": f.get("format_id", ""),
            "ext": f.get("ext", ""),
            "resolution": f.get("resolution"),
            "fps": f.get("fps"),
            "vcodec": vcodec if vcodec != "none" else None,
            "acodec": acodec if acodec != "none" else None,
            "filesize": f.get("filesize"),
            "filesize_approx": f.get("filesize_approx"),
            "tbr": f.get("tbr"),
            "vbr": f.get("vbr"),
            "abr": f.get("abr"),
            "url": f.get("url"),
            "protocol": f.get("protocol"),
            "format_note": f.get("format_note"),
            "quality": f.get("quality"),
            "has_video": vcodec not in (None, "none"),
            "has_audio": acodec not in (None, "none"),
        })
    return result


def download_video(video_id: str, opts: Dict[str, Any]) -> Dict[str, Any]:
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    task_id = str(uuid.uuid4())
    out_template = os.path.join(settings.DOWNLOAD_DIR, f"{task_id}_%(title)s.%(ext)s")
    ydl_opts = _make_ydl_opts({
        **opts,
        "outtmpl": out_template,
        "quiet": True,
    })
    url = normalize_id(video_id)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return {"task_id": task_id, "info": info, "filename": filename}
    except yt_dlp.utils.DownloadError as e:
        raise ExtractionError(str(e))


def get_direct_url(video_id: str, format_id: Optional[str] = None, quality: str = "best") -> Dict[str, Any]:
    url = normalize_id(video_id)
    fmt = format_id or f"bestvideo[height<={quality.replace('p','')}]+bestaudio/best" if quality != "best" else "best"
    if format_id:
        fmt = format_id
    opts = {"format": fmt}
    info = extract_info(url, opts)
    fmts = info.get("formats", [])
    selected = fmts[-1] if fmts else {}
    return {
        "video_id": info.get("id"),
        "title": info.get("title"),
        "direct_url": selected.get("url") or info.get("url"),
        "ext": selected.get("ext") or info.get("ext"),
        "format_id": selected.get("format_id") or "best",
        "filesize": selected.get("filesize") or selected.get("filesize_approx"),
    }


def search_videos(query: str, opts: Optional[Dict[str, Any]] = None, limit: int = 20) -> List[Dict[str, Any]]:
    search_url = f"ytsearch{limit}:{query}"
    extract_opts = _make_ydl_opts({"extract_flat": True, "quiet": True})
    if opts:
        extract_opts.update(opts)
    try:
        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            entries = info.get("entries", []) if info else []
            return [e for e in entries if e]
    except Exception as e:
        raise ExtractionError(str(e))


def get_channel_videos(channel_url: str, limit: int = 20) -> Dict[str, Any]:
    opts = {
        "extract_flat": True,
        "playlistend": limit,
        "quiet": True,
    }
    info = extract_info(channel_url + "/videos", opts)
    return info


def get_playlist_info(playlist_url: str, limit: int = 50) -> Dict[str, Any]:
    opts = {
        "extract_flat": True,
        "playlistend": limit,
        "quiet": True,
    }
    return extract_info(playlist_url, opts)


def get_comments(video_url: str, limit: int = 20, sort_by: str = "top") -> List[Dict[str, Any]]:
    opts = {
        "getcomments": True,
        "extractor_args": {
            "youtube": {
                "max_comments": [str(limit)],
                "comment_sort": [sort_by],
            }
        },
        "quiet": True,
    }
    info = extract_info(video_url, opts)
    return info.get("comments", []) or []


def get_subtitles_content(video_url: str, lang: str = "en", fmt: str = "vtt", auto: bool = True) -> Dict[str, Any]:
    os.makedirs(settings.SUBTITLE_DIR, exist_ok=True)
    task_id = str(uuid.uuid4())
    out_template = os.path.join(settings.SUBTITLE_DIR, f"{task_id}_%(title)s.%(ext)s")
    opts = {
        "writesubtitles": True,
        "writeautomaticsub": auto,
        "subtitleslangs": [lang],
        "subtitlesformat": fmt,
        "skip_download": True,
        "outtmpl": out_template,
        "quiet": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            # Find the written subtitle file
            for f in os.listdir(settings.SUBTITLE_DIR):
                if task_id in f:
                    filepath = os.path.join(settings.SUBTITLE_DIR, f)
                    with open(filepath, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    return {
                        "filepath": filepath,
                        "filename": f,
                        "content": content,
                        "info": info,
                    }
            return {"filepath": None, "filename": None, "content": "", "info": info}
    except Exception as e:
        raise ExtractionError(str(e))
