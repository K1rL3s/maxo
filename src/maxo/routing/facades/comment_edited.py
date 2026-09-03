from maxo.routing.facades.base import BaseUpdateFacade
from maxo.types.comment_edited import CommentEdited
from maxo.types.comment_message import CommentMessage
from maxo.types.facades.comment import CommentMethodsFacade


class CommentEditedFacade(BaseUpdateFacade[CommentEdited], CommentMethodsFacade):
    @property
    def message(self) -> CommentMessage:
        return self._update.message
