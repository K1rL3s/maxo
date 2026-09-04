from abc import abstractmethod

from maxo.omit import Omittable, Omitted, is_not_omitted
from maxo.types.callback import Callback
from maxo.types.facades.subscription import SubscriptionMethodsFacade
from maxo.types.new_message_body import NewMessageBody
from maxo.types.simple_query_result import SimpleQueryResult


class CallbackMethodsFacade(SubscriptionMethodsFacade):
    __slots__ = ()

    @property
    @abstractmethod
    def callback(self) -> Callback:
        raise NotImplementedError

    async def callback_answer(
        self,
        notification: Omittable[str | None] = Omitted(),
        text: Omittable[str | None] = Omitted(),  # Подражание aiogram
        message: NewMessageBody | None = None,
        disable_link_preview: Omittable[bool] = Omitted(),
    ) -> SimpleQueryResult:
        """
        Ответ на колбэк.

        Args:
            notification: Заполните это, если хотите просто отправить
                          одноразовое уведомление пользователю.
            text: Алиас для notification, подражание aiogram.
                  Используется notification или он, преимущество у notification.
            message: Заполните это, если хотите изменить текущее сообщение
            disable_link_preview: Если `true`, сервер не будет генерировать
                превью для ссылок в тексте сообщения или поста

        """
        return await self.bot.answer_on_callback(
            callback_id=self.callback.callback_id,
            notification=notification if is_not_omitted(notification) else text,
            message=message,
            disable_link_preview=disable_link_preview,
        )

    answer = callback_answer  # Подражание aiogram
