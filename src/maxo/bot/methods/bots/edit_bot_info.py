from typing_extensions import deprecated

from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body
from maxo.omit import Omittable, Omitted
from maxo.types.bot_command import BotCommand
from maxo.types.bot_info import BotInfo
from maxo.types.photo_attachment_request_payload import PhotoAttachmentRequestPayload


# Самодельный объект
@deprecated("PATCH /me нет в API MAX, команды задаёт EditMyCommands", stacklevel=2)
class EditBotInfo(MaxoMethod[BotInfo]):
    """
    Изменение информации о текущем боте.

    Позволяет изменить информацию о текущем боте.
    Заполняйте только те поля, которые требуется обновить.
    Все остальные останутся без изменений.

    Источник: https://dev.max.ru/docs-api/methods/PATCH/me

    Args:
        first_name: Отображаемое имя бота. От 1 до 64 символов
        last_name: Отображаемое второе имя бота. От 1 до 64 символов
        description: Описание бота. от 1 до 16000 символов
        commands: Команды, поддерживаемые ботом.
            Чтобы удалить все команды, передайте пустой список.
            До 32 элементов
        photo: Запрос на установку фото бота
    """

    __url__ = "me"
    __method__ = "patch"

    first_name: Body[Omittable[str | None]] = Omitted()
    last_name: Body[Omittable[str | None]] = Omitted()
    description: Body[Omittable[str | None]] = Omitted()
    commands: Body[Omittable[list[BotCommand] | None]] = Omitted()
    photo: Body[Omittable[PhotoAttachmentRequestPayload | None]] = Omitted()
