from enum import StrEnum


class VideoType(StrEnum):
    """
    Тип видео:
        - `"video"` - обычное видео
        - `"video_message"` - видеосообщение
    """

    VIDEO = "video"
    VIDEO_MESSAGE = "video_message"
