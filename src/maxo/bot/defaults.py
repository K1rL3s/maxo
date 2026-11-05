from maxo.enums import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.types import MaxoType


class BotDefaults(MaxoType):
    """Default values for bot API calls."""

    text_format: Omittable[TextFormat | None] = None
    """Default text format for messages"""
    disable_link_preview: Omittable[bool] = Omitted()
    """Default value for disable_link_preview parameter"""
