from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.chat_members_list import ChatMembersList


class GetAdmins(MaxoMethod[ChatMembersList]):
    """
    Получение списка администраторов группового чата или канала

    Возвращает список всех администраторов группового чата и канала (пользователей и ботов) и их данные, например: идентификатор, имя, никнейм, время последней активности, URL аватара, флаги администратора, владельца и бота, а также права на управление каналом или групповым чатом для пользователей-администраторов

    Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала. Подробнее о правах - в описании объекта [`Chat`](https://dev.max.ru/docs-api/objects/Chat)

    Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/chats/{chatId}/members/admins" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID группового чата или канала

    Источник: https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins
    """

    __url__ = "chats/{chat_id}/members/admins"
    __method__ = "get"

    chat_id: Path[int]
    """ID группового чата или канала"""
