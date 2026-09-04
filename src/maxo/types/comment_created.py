from maxo.enums.update_type import UpdateType
from maxo.types.base import MaxUpdate
from maxo.types.comment_message import CommentMessage
from maxo.types.facades.comment import CommentMethodsFacade


class CommentCreated(MaxUpdate, CommentMethodsFacade):
    """
    Вы получите это событие, как только комментарий будет создан

    Args:
        message: Новый созданный комментарий
        type:
    """

    type = UpdateType.COMMENT_CREATED

    message: CommentMessage
    """Новый созданный комментарий"""
