from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path, Query
from maxo.omit import Omittable, Omitted
from maxo.types.chat_members_list import ChatMembersList


class GetMembers(MaxoMethod[ChatMembersList]):
    """
    Получение участников группового чата или канала

    Возвращает список участников группового чата и их данные, например: идентификатор, имя, никнейм, время последней активности, URL аватара, флаги администратора, владельца и бота, а также права на управление каналом или групповым чатом для пользователей-администраторов. Подробнее о правах - в описании объекта [`Chat`](https://dev.max.ru/docs-api/objects/Chat)

    Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала 

    Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/chats/{chatId}/members" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID группового чата или канала
        count: Количество участников, которых нужно вернуть в ответе
        marker: Указатель на следующую страницу данных
        user_ids: Список ID пользователей, чьё членство нужно получить. Когда этот параметр передан, параметры `count` и `marker` игнорируются

    Источник: https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members
    """

    __url__ = "chats/{chat_id}/members"
    __method__ = "get"

    chat_id: Path[int]
    """ID группового чата или канала"""

    count: Query[Omittable[int]] = Omitted()
    """Количество участников, которых нужно вернуть в ответе"""
    marker: Query[Omittable[int]] = Omitted()
    """Указатель на следующую страницу данных"""
    user_ids: Query[Omittable[list[int] | None]] = Omitted()
    """Список ID пользователей, чьё членство нужно получить. Когда этот параметр передан, параметры `count` и `marker` игнорируются"""
