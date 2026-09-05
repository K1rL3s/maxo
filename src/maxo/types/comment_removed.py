from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade


class CommentRemoved(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только комментарий будет удалён

    Args:
        chat_id: ID чата, где комментарий был удалён
        message_id: ID удалённого комментария
        post_id: Идентификатор поста в канале
        type:
        user_id: Пользователь, удаливший комментарий
    """

    type = UpdateType.COMMENT_REMOVED

    chat_id: int
    """ID чата, где комментарий был удалён"""
    message_id: str
    """ID удалённого комментария"""
    user_id: int
    """Пользователь, удаливший комментарий"""

    post_id: str | None = None
    """Идентификатор поста в канале"""

    @property
    def unsafe_post_id(self) -> str:
        if is_defined(self.post_id):
            return self.post_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="post_id",
        )
