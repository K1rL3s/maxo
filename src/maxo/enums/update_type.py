from enum import StrEnum


class UpdateType(StrEnum):
    """
    Объект `Update` описывает возможные события в чате или канале. Может возвращаться в следующих случаях:
        - Вы подписались на обновления через Webhook - при наступлении события МАКС пришлёт [POST-запрос `/subscriptions`](https://dev.max.ru/docs-api/methods/POST/subscriptions), который содержит объект `Update`
        - Вы отправили [GET-запрос /updates](https://dev.max.ru/docs-api/methods/GET/updates) для получения обновлений через  Long Polling- в ответ вернётся объект `Update`

    >! Получение обновлений с помощью [Long Polling](/docs-api/methods/GET/updates) ограничено по скорости и сроку хранения событий - этот способ не подходит для production-окружения. Рекомендуем на всех этапах работы использовать [Webhook](https://dev.max.ru/docs-api/methods/POST/subscriptions)

    ## Типы событий
        - `bot_added` - бот добавлен в чат или канал
        - `bot_started` - пользователь впервые начал общение с ботом или возобновил после остановки - нажал соответствующую кнопку в настройках бота в МАКС
        - `bot_stopped` - пользователь остановил или удалил бота через настройки бота в МАКС. Во втором случае одновременно с `bot_stopped` возвращается событие `dialog_removed`
        - `bot_removed` - бот удалён из чата или канала
        - `chat_title_changed` - пользователь изменил название чата или канала
        - `dialog_cleared` - пользователь очистил историю диалога с ботом
        - `dialog_muted` - пользователь отключил уведомления в диалоге с ботом
        - `dialog_unmuted` - пользователь включил уведомления в диалоге с ботом
        - `dialog_removed` - пользователь удалил диалог с ботом. Вместе с этим событием одновременно возвращается `bot_stopped` - при удалении диалога бот останавливается автоматически
        - `message_callback` - пользователь нажал на кнопку в чате или канале
        - `message_created` - пользователь отправил новое сообщение или опубликовал пост
        - `message_edited` - пользователь отредактировал сообщение в чате или канале
        - `message_removed` - пользователь удалил сообщение из чата или канала
        - `user_added` - в чат или канал добавлен или перешёл по ссылке новый пользователь
        - `user_removed` - пользователь удалён или покинул чат или канал

     ## Свойства объекта Update"""

    BOT_ADDED = "bot_added"
    BOT_REMOVED = "bot_removed"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    CHAT_TITLE_CHANGED = "chat_title_changed"
    DIALOG_CLEARED = "dialog_cleared"
    DIALOG_MUTED = "dialog_muted"
    DIALOG_REMOVED = "dialog_removed"
    DIALOG_UNMUTED = "dialog_unmuted"
    MESSAGE_CALLBACK = "message_callback"
    MESSAGE_CREATED = "message_created"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_REMOVED = "message_removed"
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
