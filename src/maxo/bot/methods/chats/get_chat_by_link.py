from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.chat import Chat


class GetChatByLink(MaxoMethod[Chat]):
    """
    Получение информации о канале по его ссылке

    Возвращает информацию о канале по его публичной ссылке. Метод доступен только для каналов - получить информацию о чате по публичной ссылке не получится

    Args:
        chat_link: Публичная ссылка на канал

    Источник: https://dev.max.ru/docs-api/methods/GET/chats/-chatLink-
    """

    __url__ = "chats/{chat_link}"
    __method__ = "get"

    chat_link: Path[str]
    """Публичная ссылка на канал"""
