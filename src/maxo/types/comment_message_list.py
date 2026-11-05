from maxo.types.base import MaxoType
from maxo.types.comment_message import CommentMessage


class CommentMessageList(MaxoType):
    """
    Постраничный список комментариев к посту в канале

    Args:
        messages: Список комментариев к посту в канале
    """

    messages: list[CommentMessage]
    """Список комментариев к посту в канале"""
