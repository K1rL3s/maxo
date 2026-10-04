from maxo.enums import ChatType
from maxo.errors import UnknownChatTypeError
from maxo.omit import Omittable, Omitted, is_defined


def calculate_chat_id_and_user_id(
    chat_type: ChatType,
    chat_id: Omittable[int | None],
    user_id: Omittable[int | None],
) -> tuple[Omittable[int], Omittable[int]]:
    if chat_type is ChatType.CHAT:
        # Если мы в чате, то нам не надо отправлять сообщение юзеру,
        # поэтому остаётся только chat_id
        return chat_id if is_defined(chat_id) else Omitted(), Omitted()
    if chat_type is ChatType.DIALOG:
        # Если мы в личке, то API хавает и чат, и юзера
        return (
            chat_id if is_defined(chat_id) else Omitted(),
            user_id if is_defined(user_id) else Omitted(),
        )
    if chat_type is ChatType.CHANNEL:
        # То же, что ChatType.CHAT
        return chat_id if is_defined(chat_id) else Omitted(), Omitted()
    # ChatType.PRIVATE/GROUP/SUPERGROUP - алиасы значений выше,
    # поэтому сюда исполнение не доходит.
    raise UnknownChatTypeError(chat_type)
