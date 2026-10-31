from enum import StrEnum

from maxo.backoff import BackoffConfig
from maxo.enums import UploadType
from maxo.types import MaxoType

_MIB = 1024 * 1024

_INSTANT_UPLOAD_TYPES = frozenset({UploadType.IMAGE, UploadType.VIDEO})

# Only these hosts keep a chunked upload across connections; the file host
# loses it but takes one request over 2 GiB
_RESUMABLE_TYPES = frozenset({UploadType.VIDEO, UploadType.AUDIO})

DEFAULT_NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)
DEFAULT_CHUNK_BACKOFF = BackoffConfig(
    min_delay=0.5,
    max_delay=5.0,
    factor=2.0,
    jitter=0.1,
)


class UploadMethod(StrEnum):
    """Способ загрузки медиа. Частями грузятся только видео и аудио."""

    AUTO = "auto"
    SINGLE = "single"
    RESUMABLE = "resumable"


class UploadConfig(MaxoType):
    """Как `Media` грузит файлы на файловый хост: `Media(config=...)`."""

    method: UploadMethod = UploadMethod.AUTO
    resumable_threshold: int = 50 * _MIB

    chunk_size: int = 50 * _MIB
    chunk_retries: int = 3
    chunk_backoff: BackoffConfig = DEFAULT_CHUNK_BACKOFF

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("`chunk_size` should be greater than 0")
        if self.chunk_retries < 0:
            raise ValueError("`chunk_retries` should not be negative")
        if self.resumable_threshold < 0:
            raise ValueError("`resumable_threshold` should not be negative")

    def should_use_resumable(self, upload_type: UploadType, size: int) -> bool:
        """Грузить ли частями."""
        if upload_type not in _RESUMABLE_TYPES:
            return False
        if self.method is UploadMethod.RESUMABLE:
            return True
        if self.method is UploadMethod.SINGLE:
            return False
        return size >= self.resumable_threshold


class ProcessingConfig(MaxoType):
    """
    Как `Bot` ждёт обработки загруженного файла сервером: `Bot(processing=...)`.

    `build_attachments` выжидает оценку `estimated_delay`, а если сервер всё
    равно ответил `attachment.not.ready`, запрос повторяется с backoff.
    """

    not_ready_backoff: BackoffConfig = DEFAULT_NOT_READY_BACKOFF
    not_ready_max_retries: int = 10

    base_delay: float = 0.5
    delay_per_mib: float = 0.008
    max_delay: float = 30.0

    def __post_init__(self) -> None:
        if self.not_ready_max_retries < 0:
            raise ValueError("`not_ready_max_retries` should not be negative")
        if self.base_delay < 0:
            raise ValueError("`base_delay` should not be negative")
        if self.delay_per_mib < 0:
            raise ValueError("`delay_per_mib` should not be negative")
        if self.max_delay < 0:
            raise ValueError("`max_delay` should not be negative")

    def estimated_delay(self, upload_type: UploadType, size: int) -> float:
        if upload_type in _INSTANT_UPLOAD_TYPES:
            return 0.0
        delay = self.base_delay + self.delay_per_mib * (size / _MIB)
        return min(delay, self.max_delay)
