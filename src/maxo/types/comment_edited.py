from maxo.enums.update_type import UpdateType
from maxo.types.base import MaxUpdate
from maxo.types.comment_message import CommentMessage
from maxo.types.facades import CommentMethodsFacade


class CommentEdited(MaxUpdate, CommentMethodsFacade):
    """
    Вы получите это событие, как только пользователь отредактирует комментарий

    Args:
        message: Отредактированный комментарий
        type:
    """

    type = UpdateType.COMMENT_EDITED

    message: CommentMessage
    """Отредактированный комментарий"""
