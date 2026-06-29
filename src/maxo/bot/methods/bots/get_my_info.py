from maxo.bot.methods.base import MaxoMethod
from maxo.types.bot_info import BotInfo


class GetMyInfo(MaxoMethod[BotInfo]):
    """
    Получение информации о боте

    Метод возвращает информацию о боте, который идентифицируется с помощью токена доступа `access_token`. В ответе приходит [объект User с вариантом наследования BotInfo](https://dev.max.ru/docs-api/objects/User), который содержит идентификатор бота, его название, никнейм, время последней активности, описание и аватар (при наличии)

    #### Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/me" \
      -H "Authorization: {access_token}"
    ```

    Источник: https://dev.max.ru/docs-api/methods/GET/me
    """

    __url__ = "me"
    __method__ = "get"
