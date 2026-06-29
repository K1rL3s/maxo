from maxo import Router
from maxo.routing.updates import MessageCreated

echo_router = Router(__name__)


@echo_router.message_created()
async def echo_handler(message: MessageCreated) -> None:
    text = message.message.body.text or "Текста нет"
    await message.answer_text(text)
