from maxo.routing.facades.base import BaseUpdateFacade
from maxo.types.comment_created import CommentCreated
from maxo.types.comment_message import CommentMessage
from maxo.types.facades.comment import CommentMethodsFacade


class CommentCreatedFacade(BaseUpdateFacade[CommentCreated], CommentMethodsFacade):
    @property
    def message(self) -> CommentMessage:
        return self._update.message
