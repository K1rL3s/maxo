from maxo.routing.facades.base import BaseUpdateFacade
from maxo.types.comment_removed import CommentRemoved
from maxo.types.facades.chat import ChatMethodsFacade


class CommentRemovedFacade(BaseUpdateFacade[CommentRemoved], ChatMethodsFacade):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def message_id(self) -> str:
        return self._update.message_id

    @property
    def post_id(self) -> str | None:
        return self._update.post_id

    @property
    def user_id(self) -> int:
        return self._update.user_id
