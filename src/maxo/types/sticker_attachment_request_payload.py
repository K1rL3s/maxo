from maxo.types.base import MaxoType


class StickerAttachmentRequestPayload(MaxoType):
    """
    Данные для при прикрепления стикера к сообщению. Должен быть единственным вложением в сообщении. В одном запросе можно отправить только один стикер

    Args:
        code: Код стикера
    """

    code: str
    """Код стикера"""
