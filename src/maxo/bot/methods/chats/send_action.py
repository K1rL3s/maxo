from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Path
from maxo.enums.sender_action import SenderAction
from maxo.types.simple_query_result import SimpleQueryResult


class SendAction(MaxoMethod[SimpleQueryResult]):
    """
    Отправка действия бота в групповой чат

    Позволяет отправлять в групповой чат такие действия бота, как например: «набор текста» или «отправка фото»

    #### Пример запроса:
    ```bash
    curl -X POST "https://platform-api.max.ru/chats/{chatId}/actions" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
      "action": "typing_on"
    }'
    ```

    Args:
        action: 
        chat_id: ID чата

    Источник: https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/actions
    """

    __url__ = "chats/{chat_id}/actions"
    __method__ = "post"

    chat_id: Path[int]
    """ID чата"""

    action: Body[SenderAction]
