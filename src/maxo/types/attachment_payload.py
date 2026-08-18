from maxo.types.base import MaxoType


class AttachmentPayload(MaxoType):
    """
    Args:
        url: URL вложения, который возвращается в объекте [Update](https://dev.max.ru/docs-api/objects/Update) после отправки сообщения в чат или канал
             В случае с вложенным видео прямую ссылку также можно получить с помощью метода [`GET /videos/{-videoToken-}`](https://dev.max.ru/docs-api/methods/GET/videos/-videoToken-)
    """

    url: str
    """
    URL вложения, который возвращается в объекте [Update](https://dev.max.ru/docs-api/objects/Update) после отправки сообщения в чат или канал

     В случае с вложенным видео прямую ссылку также можно получить с помощью метода [`GET /videos/{-videoToken-}`](https://dev.max.ru/docs-api/methods/GET/videos/-videoToken-)
    """
