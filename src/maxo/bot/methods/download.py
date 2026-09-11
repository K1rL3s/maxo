from maxo.bot.methods.base import MaxoStreamMethod
from maxo.bot.methods.markers import Path


# Самодельный метод
class Download(MaxoStreamMethod):
    """Скачивание вложения по произвольному URL (не по шаблону API)."""

    url: Path[str]

    __url__ = "{url}"
    __method__ = "GET"
