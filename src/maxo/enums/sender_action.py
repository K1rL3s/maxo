from enum import StrEnum


class SenderAction(StrEnum):
    """
    Действие, отправляемое участникам чата. Возможные значения:
        - `"typing_on"` - Бот набирает сообщение
        - `"sending_photo"` - Бот отправляет фото
        - `"sending_video"` - Бот отправляет видео
        - `"sending_audio"` - Бот отправляет аудиофайл
        -  `"sending_file"` - Бот отправляет файл
    """

    SENDING_AUDIO = "sending_audio"
    SENDING_FILE = "sending_file"
    SENDING_PHOTO = "sending_photo"
    SENDING_VIDEO = "sending_video"
    TYPING_ON = "typing_on"

    MARK_SEEN = "mark_seen"  # Удалён из доки, работает
