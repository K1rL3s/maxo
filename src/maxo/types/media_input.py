from typing import TypeAlias

from maxo.types.attachments import MediaAttachmentsRequests
from maxo.utils.upload_media import InputFile

MediaInput: TypeAlias = InputFile | MediaAttachmentsRequests
"""Медиа для отправки: файл, который надо загрузить, или готовое вложение."""
