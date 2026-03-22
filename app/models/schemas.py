"""
ytworkflo — Pydantic Models
All request/response schemas are defined here.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class SearchOrder(str, Enum):
    relevance = "relevance"
    date = "date"
    views = "views"
    rating = "rating"
    title = "title"

class SearchFilter(str, Enum):
    video = "video"
    channel = "channel"
    playlist = "playlist"
    movie = "movie"
    live = "live"

class VideoQuality(str, Enum):
    best = "best"
    worst = "worst"
    q2160p = "2160p"
    q1440p = "1440p"
    q1080p = "1080p"
    q720p = "720p"
    q480p = "480p"
    q360p = "360p"
    q240p = "240p"
    q144p = "144p"

class AudioFormat(str, Enum):
    mp3 = "mp3"
    aac = "aac"
    opus = "opus"
    flac = "flac"
    wav = "wav"
    m4a = "m4a"
    vorbis = "vorbis"
    best = "best"

class SubtitleFormat(str, Enum):
    vtt = "vtt"
    srt = "srt"
    json3 = "json3"
    ass = "ass"
    ttml = "ttml"
    srv1 = "srv1"
    srv2 = "srv2"
    srv3 = "srv3"

class TrendingCategory(str, Enum):
    default = "0"
    music = "10"
    gaming = "20"
    movies = "30"
    news = "25"
    sports = "17"
    science_tech = "28"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


# ─────────────────────────────────────────────
# Shared / Common
# ─────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")

class PaginatedMeta(BaseModel):
    page: int
    per_page: int
    total: Optional[int] = None
    has_more: bool = False

class ThumbnailItem(BaseModel):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    resolution: Optional[str] = None

class Chapter(BaseModel):
    title: str
    start_time: float
    end_time: Optional[float] = None

class Subtitle(BaseModel):
    language: str
    language_code: str
    url: Optional[str] = None
    is_auto_generated: bool = False

class Heatmap(BaseModel):
    start_time: float
    end_time: float
    value: float

class ErrorResponse(BaseModel):
    error: str
    status_code: int


# ─────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filter: Optional[SearchFilter] = Field(None, description="Filter result type")
    order: SearchOrder = Field(SearchOrder.relevance, description="Sort order")
    language: Optional[str] = Field(None, description="ISO 639-1 language code, e.g. 'en'")
    region: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 region code, e.g. 'US'")
    safe_search: bool = Field(False, description="Enable safe search")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=50)

class SearchResultItem(BaseModel):
    id: str
    type: str  # "video" | "channel" | "playlist"
    title: str
    url: str
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    published_at: Optional[str] = None
    channel_name: Optional[str] = None
    channel_id: Optional[str] = None
    view_count: Optional[int] = None
    duration: Optional[int] = None
    duration_string: Optional[str] = None
    is_live: bool = False

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    meta: PaginatedMeta


# ─────────────────────────────────────────────
# Video
# ─────────────────────────────────────────────

class VideoRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID or full URL")

class VideoFormat(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    filesize_approx: Optional[int] = None
    tbr: Optional[float] = None
    vbr: Optional[float] = None
    abr: Optional[float] = None
    url: Optional[str] = None
    protocol: Optional[str] = None
    format_note: Optional[str] = None
    quality: Optional[float] = None
    has_video: bool = False
    has_audio: bool = False

class VideoInfo(BaseModel):
    id: str
    title: str
    url: str
    description: Optional[str] = None
    duration: Optional[int] = None
    duration_string: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    channel_url: Optional[str] = None
    channel_follower_count: Optional[int] = None
    upload_date: Optional[str] = None
    timestamp: Optional[int] = None
    is_live: bool = False
    was_live: bool = False
    categories: List[str] = []
    tags: List[str] = []
    age_limit: int = 0
    language: Optional[str] = None
    thumbnails: List[ThumbnailItem] = []
    chapters: List[Chapter] = []
    subtitles: Dict[str, List[Any]] = {}
    automatic_captions: Dict[str, List[Any]] = {}
    heatmap: List[Heatmap] = []
    formats: List[VideoFormat] = []
    webpage_url: Optional[str] = None
    extractor: str = "youtube"
    availability: Optional[str] = None


# ─────────────────────────────────────────────
# Channel
# ─────────────────────────────────────────────

class ChannelRequest(BaseModel):
    channel_id: str = Field(..., description="Channel ID, handle (@name), or URL")

class ChannelVideosRequest(BaseModel):
    channel_id: str
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=50)
    order: SearchOrder = SearchOrder.date

class ChannelInfo(BaseModel):
    id: str
    name: str
    url: str
    handle: Optional[str] = None
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    country: Optional[str] = None
    joined_date: Optional[str] = None
    thumbnails: List[ThumbnailItem] = []
    banners: List[ThumbnailItem] = []
    channel_tabs: List[str] = []
    tags: List[str] = []
    is_verified: bool = False

class ChannelVideosResponse(BaseModel):
    channel_id: str
    channel_name: str
    videos: List[SearchResultItem]
    meta: PaginatedMeta


# ─────────────────────────────────────────────
# Playlist
# ─────────────────────────────────────────────

class PlaylistRequest(BaseModel):
    playlist_id: str = Field(..., description="Playlist ID or full URL")

class PlaylistInfo(BaseModel):
    id: str
    title: str
    url: str
    description: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    view_count: Optional[int] = None
    modified_date: Optional[str] = None
    entry_count: Optional[int] = None
    thumbnails: List[ThumbnailItem] = []
    availability: Optional[str] = None

class PlaylistVideosResponse(BaseModel):
    playlist: PlaylistInfo
    videos: List[SearchResultItem]
    meta: PaginatedMeta


# ─────────────────────────────────────────────
# Download
# ─────────────────────────────────────────────

class DownloadRequest(BaseModel):
    video_id: str = Field(..., description="Video ID or URL")
    quality: VideoQuality = Field(VideoQuality.best, description="Video quality")
    format_id: Optional[str] = Field(None, description="Specific format ID to download")
    audio_only: bool = Field(False, description="Download audio only")
    audio_format: AudioFormat = Field(AudioFormat.mp3, description="Audio format if audio_only")
    embed_subs: bool = Field(False, description="Embed subtitles into video")
    embed_thumbnail: bool = Field(False, description="Embed thumbnail into file")
    add_metadata: bool = Field(True, description="Add metadata tags")
    subtitle_lang: Optional[str] = Field(None, description="Subtitle language code to embed")

class DownloadResponse(BaseModel):
    task_id: str
    video_id: str
    title: str
    filename: str
    filepath: str
    filesize: Optional[int] = None
    format: str
    ext: str
    status: str  # "completed" | "pending" | "failed"
    message: Optional[str] = None

class DownloadURLResponse(BaseModel):
    video_id: str
    title: str
    direct_url: str
    ext: str
    format_id: str
    filesize: Optional[int] = None
    expires_approx: Optional[str] = None


# ─────────────────────────────────────────────
# Stream
# ─────────────────────────────────────────────

class StreamRequest(BaseModel):
    video_id: str
    quality: VideoQuality = VideoQuality.best
    format_id: Optional[str] = None

class StreamInfo(BaseModel):
    video_id: str
    title: str
    stream_url: str
    ext: str
    format_id: str
    resolution: Optional[str] = None
    fps: Optional[float] = None
    tbr: Optional[float] = None
    is_live: bool = False
    manifest_url: Optional[str] = None
    hls_url: Optional[str] = None
    dash_url: Optional[str] = None

class LiveStreamInfo(BaseModel):
    video_id: str
    title: str
    is_live: bool
    stream_url: Optional[str] = None
    hls_url: Optional[str] = None
    dash_url: Optional[str] = None
    concurrent_viewers: Optional[int] = None
    started_at: Optional[str] = None


# ─────────────────────────────────────────────
# Audio
# ─────────────────────────────────────────────

class AudioExtractRequest(BaseModel):
    video_id: str
    format: AudioFormat = AudioFormat.mp3
    quality: str = Field("192", description="Bitrate in kbps, e.g. '192', '320', 'best'")
    start_time: Optional[float] = Field(None, description="Trim start (seconds)")
    end_time: Optional[float] = Field(None, description="Trim end (seconds)")
    normalize: bool = Field(False, description="Normalize audio volume")

class AudioInfo(BaseModel):
    video_id: str
    title: str
    filename: str
    filepath: str
    format: str
    bitrate: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    duration: Optional[float] = None
    filesize: Optional[int] = None

class AudioStreamRequest(BaseModel):
    video_id: str
    format: AudioFormat = AudioFormat.best

class AudioStreamInfo(BaseModel):
    video_id: str
    title: str
    stream_url: str
    ext: str
    abr: Optional[float] = None
    asr: Optional[int] = None
    acodec: Optional[str] = None


# ─────────────────────────────────────────────
# Transcript
# ─────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    video_id: str
    language: str = Field("en", description="Language code, e.g. 'en', 'hi'")
    auto_generated: bool = Field(True, description="Allow auto-generated captions")
    translate_to: Optional[str] = Field(None, description="Translate transcript to language code")

class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float
    end: float

class TranscriptResponse(BaseModel):
    video_id: str
    title: str
    language: str
    language_code: str
    is_auto_generated: bool
    segments: List[TranscriptSegment]
    full_text: str
    translated_to: Optional[str] = None

class TranscriptListResponse(BaseModel):
    video_id: str
    available_languages: List[Subtitle]


# ─────────────────────────────────────────────
# Thumbnails
# ─────────────────────────────────────────────

class ThumbnailsResponse(BaseModel):
    video_id: str
    title: str
    thumbnails: List[ThumbnailItem]
    best: Optional[ThumbnailItem] = None

class ThumbnailDownloadRequest(BaseModel):
    video_id: str
    resolution: Optional[str] = Field(None, description="'maxres', 'hq', 'mq', 'default'")


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

class EngagementMetrics(BaseModel):
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    like_ratio: Optional[float] = None
    engagement_rate: Optional[float] = None
    views_per_day: Optional[float] = None
    estimated_reach: Optional[str] = None

class VideoAnalytics(BaseModel):
    video_id: str
    title: str
    upload_date: Optional[str] = None
    duration: Optional[int] = None
    age_days: Optional[int] = None
    engagement: EngagementMetrics
    heatmap: List[Heatmap] = []
    top_moments: List[Dict[str, Any]] = []
    performance_score: Optional[float] = None
    tags: List[str] = []
    categories: List[str] = []

class ChannelAnalytics(BaseModel):
    channel_id: str
    channel_name: str
    subscriber_count: Optional[int] = None
    total_views: Optional[int] = None
    video_count: Optional[int] = None
    avg_views_per_video: Optional[float] = None
    estimated_monthly_views: Optional[float] = None


# ─────────────────────────────────────────────
# Batch
# ─────────────────────────────────────────────

class BatchVideoRequest(BaseModel):
    video_ids: List[str] = Field(..., min_length=1, max_length=50)
    include_formats: bool = Field(False, description="Include format list in response")

class BatchVideoResponse(BaseModel):
    requested: int
    succeeded: int
    failed: int
    results: List[Union[VideoInfo, Dict[str, str]]]

class BatchDownloadRequest(BaseModel):
    video_ids: List[str] = Field(..., min_length=1, max_length=20)
    quality: VideoQuality = VideoQuality.best
    audio_only: bool = False
    audio_format: AudioFormat = AudioFormat.mp3

class BatchDownloadResponse(BaseModel):
    task_id: str
    requested: int
    status: str
    items: List[DownloadResponse]

class BatchTranscriptRequest(BaseModel):
    video_ids: List[str] = Field(..., min_length=1, max_length=20)
    language: str = "en"
    auto_generated: bool = True


# ─────────────────────────────────────────────
# Formats
# ─────────────────────────────────────────────

class FormatsResponse(BaseModel):
    video_id: str
    title: str
    formats: List[VideoFormat]
    best_video: Optional[VideoFormat] = None
    best_audio: Optional[VideoFormat] = None
    best_combined: Optional[VideoFormat] = None

class FormatFilterRequest(BaseModel):
    video_id: str
    ext: Optional[str] = Field(None, description="Filter by extension, e.g. 'mp4', 'webm'")
    min_height: Optional[int] = None
    max_height: Optional[int] = None
    has_video: Optional[bool] = None
    has_audio: Optional[bool] = None
    min_fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None


# ─────────────────────────────────────────────
# Comments
# ─────────────────────────────────────────────

class CommentsRequest(BaseModel):
    video_id: str
    sort_by: str = Field("top", description="'top' or 'new'")
    limit: int = Field(20, ge=1, le=200)

class CommentItem(BaseModel):
    id: str
    author: str
    author_id: Optional[str] = None
    text: str
    timestamp: Optional[int] = None
    like_count: Optional[int] = None
    reply_count: Optional[int] = None
    is_pinned: bool = False
    is_favorited: bool = False
    parent_id: Optional[str] = None

class CommentsResponse(BaseModel):
    video_id: str
    title: str
    comment_count: Optional[int] = None
    comments: List[CommentItem]
    meta: PaginatedMeta


# ─────────────────────────────────────────────
# Trending
# ─────────────────────────────────────────────

class TrendingRequest(BaseModel):
    region: str = Field("US", description="ISO 3166-1 alpha-2 region code")
    category: TrendingCategory = Field(TrendingCategory.default, description="Category ID")
    limit: int = Field(20, ge=1, le=50)

class TrendingResponse(BaseModel):
    region: str
    category: str
    fetched_at: str
    videos: List[SearchResultItem]


# ─────────────────────────────────────────────
# Subtitles
# ─────────────────────────────────────────────

class SubtitleDownloadRequest(BaseModel):
    video_id: str
    language: str = Field("en", description="Language code")
    format: SubtitleFormat = Field(SubtitleFormat.srt, description="Output format")
    auto_generated: bool = Field(True, description="Allow auto-generated captions")

class SubtitleDownloadResponse(BaseModel):
    video_id: str
    language: str
    format: str
    filename: str
    filepath: str
    content_preview: Optional[str] = Field(None, description="First 500 chars of subtitle")

class SubtitleContentResponse(BaseModel):
    video_id: str
    language: str
    format: str
    content: str
    segments: List[TranscriptSegment] = []
