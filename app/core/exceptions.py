from fastapi import Request
from fastapi.responses import JSONResponse


class YTWorkfloError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class VideoNotFoundError(YTWorkfloError):
    def __init__(self, video_id: str):
        super().__init__(f"Video '{video_id}' not found or unavailable.", 404)


class ChannelNotFoundError(YTWorkfloError):
    def __init__(self, channel_id: str):
        super().__init__(f"Channel '{channel_id}' not found.", 404)


class PlaylistNotFoundError(YTWorkfloError):
    def __init__(self, playlist_id: str):
        super().__init__(f"Playlist '{playlist_id}' not found.", 404)


class ExtractionError(YTWorkfloError):
    def __init__(self, detail: str):
        super().__init__(f"Extraction failed: {detail}", 502)


class UnsupportedFormatError(YTWorkfloError):
    def __init__(self, fmt: str):
        super().__init__(f"Format '{fmt}' is not supported.", 422)


async def ytworkflo_exception_handler(request: Request, exc: YTWorkfloError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code},
    )
