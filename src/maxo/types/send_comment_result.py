from maxo.types.base import MaxoType
from maxo.types.comment_message import CommentMessage


class SendCommentResult(MaxoType):
    """
    Результат отправки комментария

    Args:
        message:
    """

    message: CommentMessage
