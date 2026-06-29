from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.video_attachment_details import VideoAttachmentDetails


class GetVideoAttachmentDetails(MaxoMethod[VideoAttachmentDetails]):
    """
    Получить информацию о видео

    Возвращает подробную информацию о прикреплённом видео, URL-адреса воспроизведения и дополнительные метаданные

    #### Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/videos/{video_token}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        video_token: Токен видео-вложения

    Источник: https://dev.max.ru/docs-api/methods/GET/videos/-videoToken-
    """

    __url__ = "videos/{video_token}"
    __method__ = "get"

    video_token: Path[str]
    """Токен видео-вложения"""
