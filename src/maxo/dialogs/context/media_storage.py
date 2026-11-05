from pathlib import Path
from typing import NamedTuple

from cachetools import LRUCache

from maxo.dialogs.api.entities import MediaId
from maxo.dialogs.api.protocols import MediaIdStorageProtocol
from maxo.enums import AttachmentType


class CachedMediaId(NamedTuple):
    media_id: MediaId
    mtime: float | None


class MediaIdStorage(MediaIdStorageProtocol):
    def __init__(self, maxsize: int = 1024) -> None:
        self.cache: LRUCache[
            tuple[str | None, str | None, AttachmentType],
            CachedMediaId,
        ] = LRUCache(maxsize=maxsize)

    async def get_media_id(
        self,
        path: Path | str | None,
        url: str | None,
        type: AttachmentType,
    ) -> MediaId | None:
        if not path and not url:
            return None
        key = (str(path) if path else None, url, type)
        cached: CachedMediaId | None = self.cache.get(key)
        if cached is None:
            return None

        if cached.mtime is not None:
            mtime = self._get_file_mtime(path)
            if mtime is not None and mtime != cached.mtime:
                return None
        return cached.media_id

    def _get_file_mtime(self, path: Path | str | None) -> float | None:
        if not path:
            return None
        path = Path(path)
        if not path.exists():
            return None
        return path.stat().st_mtime

    async def save_media_id(
        self,
        path: Path | str | None,
        url: str | None,
        type: AttachmentType,
        media_id: MediaId,
    ) -> None:
        if not path and not url:
            return
        key = (str(path) if path else None, url, type)
        self.cache[key] = CachedMediaId(
            media_id,
            self._get_file_mtime(path),
        )
