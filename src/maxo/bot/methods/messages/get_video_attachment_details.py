from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.video_attachment_details import VideoAttachmentDetails


class GetVideoAttachmentDetails(MaxoMethod[VideoAttachmentDetails]):
    """
    Получение информации о видео, прикреплённом к сообщению

    Возвращает подробную информацию о видео, прикреплённом к сообщению в чате или канале, URL-адреса воспроизведения и дополнительные метаданные

    #### Пример запроса:
    ```bash
    curl -X GET "https://platform-api2.max.ru/videos/{video_token}" \
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
