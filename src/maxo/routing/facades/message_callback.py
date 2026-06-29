from maxo.omit import Omittable
from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import MessageMethodsFacade
from maxo.routing.mixins.callback import CallbackMethodsFacade
from maxo.routing.updates.message_callback import MessageCallback
from maxo.types.callback import Callback
from maxo.types.message import Message
from maxo.types.user import User


class MessageCallbackFacade(
    BaseUpdateFacade[MessageCallback],
    CallbackMethodsFacade,
    MessageMethodsFacade,
):
    @property
    def message(self) -> Message:
        return self._update.unsafe_message

    @property
    def callback(self) -> Callback:
        return self._update.callback

    @property
    def user_locale(self) -> Omittable[str | None]:
        return self._update.user_locale

    @property
    def callback_id(self) -> str:
        return self._update.callback_id

    @property
    def payload(self) -> Omittable[str]:
        return self._update.payload

    @property
    def user(self) -> User:
        return self._update.user
