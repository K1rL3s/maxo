"""
Декларативные таблицы maxo-профиля.

Здесь только данные - всё, чем maxo намеренно отличается от свагера. Логика
живёт в :mod:`butcher.profile`. Если после генерации приходится править файл
руками одинаковым образом - место правки здесь, а не в `src/maxo`.
"""

from dataclasses import dataclass, field

# --- пропуски ----------------------------------------------------------------

SKIP_SCHEMAS: frozenset[str] = frozenset(
    {
        # Reply-клавиатуры: клиенты MAX их не поддерживают. Пропуск `ReplyButton`
        # каскадом убирает его подтипы и enum `ReplyButtonType`.
        "ReplyButton",
        "ReplyKeyboardAttachment",
        "ReplyKeyboardAttachmentRequest",
        # Тела запросов: генератор размазывает их по `Body`-полям методов,
        # отдельный тип не нужен. Список явный - `NewMessageBody` тоже тело
        # запроса, но в maxo он нужен как публичный тип.
        "ActionRequestBody",
        "BotCommandsPatch",
        "BotPatch",
        "CallbackAnswer",
        "ChatPatch",
        "PinMessageBody",
        "PhotoTokens",
        "SubscriptionRequestBody",
        "UserIdsList",
        # Нерабочая кнопка: нет `ButtonType.CHAT`, в свагере сирота.
        "ChatButton",
        # Вложение из reply-кнопки, в mapping'ах не участвует.
        "DataAttachment",
        # Ошибки API описаны вручную в `maxo.errors`.
        "Error",
        # Апдейт вне `Update.discriminator.mapping`, в maxo его нет.
        "MessageChatCreatedUpdate",
    },
)

SKIP_ENUMS: frozenset[str] = frozenset(
    {
        # Намерение кнопки: в свагере есть, ни одна схема на него не ссылается.
        "Intent",
    },
)

SKIP_OPERATIONS: frozenset[str] = frozenset(
    {
        # `GET /chats` объявлен без параметров и без ответов (метод свернули в
        # июне 2026), а рабочая версия в maxo ведётся вручную.
        "GetChats",
    },
)

# --- типы --------------------------------------------------------------------

#: Схема `bigint` - это просто int64.
INLINE_ALIASES: dict[str, str] = {"Bigint": "int", "MessageId": "str"}

#: Схемы, чей файл не генерируется, но подтипы остаются: их предком становится
#: указанный класс. В отличие от `SKIP_SCHEMAS`, каскада на наследников нет.
REPLACED_BASES: dict[str, str] = {
    # База апдейтов ведётся вручную: `MaxUpdate` в `maxo/types/base.py`.
    "Update": "MaxUpdate",
}

#: Схема-предок апдейтов - по ней профиль отличает апдейты от обычных типов.
UPDATE_BASE_SCHEMA = "Update"

#: Суффикс в именах схем-апдейтов, снимаемый с класса:
#: `MessageCreatedUpdate` -> `MessageCreated`.
UPDATE_CLASS_SUFFIX = "Update"

#: Имя, под которым дискриминатор апдейта выставляется в классе. Должно совпадать
#: с `MaxUpdate.type: ClassVar[UpdateType]` в `maxo/types/base.py`.
UPDATE_TYPE_ATTR = "type"

#: Корень иерархии типов.
ROOT_BASE_CLASS = "MaxoType"

#: Базы моделей, которыми maxo намеренно уточняет плоские схемы Swagger.
MODEL_BASE_OVERRIDES: dict[str, str] = {
    "CommentLinkedMessage": "LinkedMessage",
    "CommentMessage": "Message",
    "CommentMessageBody": "MessageBody",
}

#: Слова в описании, по которым int64 распознаётся как таймстемп.
TIMESTAMP_HINTS: tuple[str, ...] = ("time", "timestamp", "date", "время")

#: Тип поля метода там, где свагер неверен и генератор выводит `Any` (тело
#: `UserIdsList` - parameters-объект; `message_ids` - массив без `items`).
METHOD_FIELD_TYPES: dict[tuple[str, str], str] = {
    ("AddMembers", "user_ids"): "list[int]",
    ("GetMessages", "message_ids"): "list[str] | None",
}

#: Описания полей методов там, где одна wire-модель используется операциями
#: с разной семантикой
METHOD_FIELD_DESCRIPTIONS: dict[tuple[str, str], str] = {
    (
        "SendMessage",
        "attachments",
    ): "Вложения отправляемого сообщения. Пустое значение означает, что вложений нет",
}


@dataclass(slots=True, frozen=True)
class FieldOverride:
    """Ручная правка поля модели поверх того, что дал генератор."""

    ref: str | None = None
    """Заменить ссылочный тип поля и его импорт."""
    annotation: str | None = None
    """Заменить тип поля (импорты берутся от исходного типа)."""
    omittable: bool | None = None
    """Форсировать `Omittable`/обычное поле независимо от `required` в свагере."""
    comment: str | None = None
    """Хвостовой комментарий после объявления (``# ...``)."""


#: Точечные правки полей моделей там, где свагер расходится с maxo. Ключ -
#: ``(класс, поле)``.
MODEL_FIELD_OVERRIDES: dict[tuple[str, str], FieldOverride] = {
    # Swagger ссылается на Message, хотя comment update несет CommentMessage.
    ("CommentCreated", "message"): FieldOverride(ref="CommentMessage"),
    ("CommentEdited", "message"): FieldOverride(ref="CommentMessage"),
    # Wire-модель комментария сужает mutable-поле базового LinkedMessage.
    ("CommentLinkedMessage", "message"): FieldOverride(
        comment="type: ignore[mutable-override]",
    ),
    # Wire-модель комментария сужает mutable-поля базового Message.
    ("CommentMessage", "body"): FieldOverride(
        comment="type: ignore[mutable-override]",
    ),
    ("CommentMessage", "link"): FieldOverride(
        comment="type: ignore[mutable-override]",
    ),
    # Описание допускает `null`, но в Swagger нет `nullable: true`
    ("CommentMessage", "sender"): FieldOverride(annotation="User | None"),
    # CommentMessage является Message, поэтому общий контракт допускает `null`.
    ("Message", "sender"): FieldOverride(annotation="User | None"),
    # `Button.text` обязателен, но принятая кнопка может прийти без него.
    ("MessageButton", "text"): FieldOverride(
        omittable=True,
        comment="type: ignore[assignment]",
    ),
    # В свагере `photos` - map, но на деле приходит список токенов.
    ("PhotoAttachmentRequestPayload", "photos"): FieldOverride(
        annotation="list[PhotoToken] | None",
        comment="TODO: Проверить кто это",
    ),
    # Описание Swagger допускает отсутствие поля при скрытом онлайн-статусе,
    # хотя оно ошибочно осталось в required.
    ("User", "last_activity_time"): FieldOverride(omittable=True),
    # Поле объявлено устаревшим и уже может не приходить, хотя осталось в
    # required. Сужение жило в src ручной правкой - переносим в оверрайды,
    # иначе следующая генерация снесёт его вместе с `unsafe_name`.
    ("User", "name"): FieldOverride(omittable=True),
}


# --- union-алиасы ------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class UnionAlias:
    """Один алиас-объединение в файле `maxo/types/*.py`."""

    name: str
    base: str | None = None
    """Взять все подтипы этой дискриминированной базы."""
    include: tuple[str, ...] = ()
    """Добавить эти имена (классы или объявленные выше алиасы того же файла)."""
    exclude: tuple[str, ...] = ()
    """Не включать эти подтипы - обычно они уже покрыты алиасом из `include`."""
    sort: bool = True
    """Сортировать подтипы по имени; иначе - порядок из `discriminator.mapping`."""
    annotate: bool = False
    """Рендерить как ``X: TypeAlias = ...``."""


@dataclass(slots=True, frozen=True)
class UnionFile:
    """Файл `maxo/types/<module>.py` с алиасами-объединениями."""

    module: str
    aliases: tuple[UnionAlias, ...]


_MEDIA = ("PhotoAttachment", "VideoAttachment", "AudioAttachment", "FileAttachment")
_MEDIA_REQUESTS = tuple(f"{name}Request" for name in _MEDIA)

UNION_FILES: tuple[UnionFile, ...] = (
    UnionFile(
        module="attachments",
        aliases=(
            UnionAlias(name="MediaAttachments", include=_MEDIA, sort=False),
            UnionAlias(
                name="Attachments",
                base="Attachment",
                include=("MediaAttachments",),
                exclude=_MEDIA,
                sort=False,
            ),
            UnionAlias(
                name="MediaAttachmentsRequests",
                include=_MEDIA_REQUESTS,
                sort=False,
            ),
            UnionAlias(
                name="AttachmentsRequests",
                base="AttachmentRequest",
                include=("MediaAttachmentsRequests",),
                exclude=_MEDIA_REQUESTS,
                sort=False,
            ),
        ),
    ),
    UnionFile(
        module="buttons",
        aliases=(UnionAlias(name="InlineButtons", base="Button"),),
    ),
    UnionFile(
        module="markup_elements",
        aliases=(UnionAlias(name="MarkupElements", base="MarkupElement"),),
    ),
    UnionFile(
        module="updates",
        aliases=(UnionAlias(name="Updates", base="Update", annotate=True),),
    ),
)

#: Чем заменять ссылку на дискриминированную базу в аннотациях полей.
#: Значение - готовое выражение, все его имена берутся из файла алиаса.
BASE_TO_UNION: dict[str, str] = {
    "Attachment": "Attachments",
    "AttachmentRequest": "AttachmentsRequests | Attachments",
    "Button": "InlineButtons",
    "MarkupElement": "MarkupElements",
    "Update": "Updates",
}


# --- enum'ы ------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class EnumMember:
    """Дополнительный член enum поверх сгенерированных."""

    name: str
    value: str
    comment: str | None = None
    alias_of: str | None = None
    """Если задано - член-алиас: ``DOCUMENT = FILE``."""


@dataclass(slots=True, frozen=True)
class EnumExtras:
    """Ручные добавки к сгенерированному enum."""

    leading: tuple[EnumMember, ...] = ()
    trailing: tuple[EnumMember, ...] = ()
    aliases: tuple[EnumMember, ...] = ()
    aliases_comment: str | None = None
    type_aliases: tuple[tuple[str, str], ...] = ()
    """``(имя, комментарий)`` для ``Имя: TypeAlias = <Enum>`` на уровне модуля."""


_AIOGRAM = "Подражание aiogram"

ENUM_EXTRAS: dict[str, EnumExtras] = {
    "AttachmentType": EnumExtras(
        leading=(
            EnumMember(name="TEXT", value="text", comment="Самодельное поле"),
            EnumMember(name="UNKNOWN", value="unknown", comment="Самодельное поле"),
        ),
        aliases=(
            EnumMember(name="DOCUMENT", value="file", alias_of="FILE"),
            EnumMember(name="PHOTO", value="image", alias_of="IMAGE"),
        ),
        aliases_comment=_AIOGRAM,
        type_aliases=(("ContentType", _AIOGRAM),),
    ),
    "ChatAdminPermission": EnumExtras(
        trailing=(
            EnumMember(
                name="VIEW_STATS",
                value="view_stats",
                comment="Нет в доке, приходит",
            ),
        ),
    ),
    "ChatType": EnumExtras(
        aliases=(
            EnumMember(name="PRIVATE", value="dialog", alias_of="DIALOG"),
            EnumMember(name="GROUP", value="chat", alias_of="CHAT"),
            EnumMember(name="SUPERGROUP", value="chat", alias_of="CHAT"),
        ),
        aliases_comment=_AIOGRAM,
    ),
    "SenderAction": EnumExtras(
        trailing=(
            EnumMember(
                name="MARK_SEEN",
                value="mark_seen",
                comment="Удалён из доки, работает",
            ),
        ),
    ),
    "TextFormat": EnumExtras(type_aliases=(("ParseMode", _AIOGRAM),)),
}


# --- фасады ------------------------------------------------------------------

#: Миксины, которые подмешиваются в базы класса после основного предка.
CLASS_MIXINS: dict[str, tuple[str, ...]] = {
    "BotAddedToChat": ("ChatMethodsFacade",),
    "BotRemovedFromChat": ("ChatMethodsFacade",),
    "BotStarted": ("ChatMethodsFacade",),
    "BotStopped": ("ChatMethodsFacade",),
    "ChatTitleChanged": ("ChatMethodsFacade",),
    "CommentCreated": ("CommentMethodsFacade",),
    "CommentEdited": ("CommentMethodsFacade",),
    "CommentMessage": ("CommentMethodsFacade",),
    "CommentRemoved": ("ChatMethodsFacade",),
    "DialogCleared": ("ChatMethodsFacade",),
    "DialogMuted": ("ChatMethodsFacade",),
    "DialogRemoved": ("ChatMethodsFacade",),
    "DialogUnmuted": ("ChatMethodsFacade",),
    "Message": ("MessageMethodsFacade",),
    "MessageCallback": ("CallbackMethodsFacade", "MessageMethodsFacade"),
    "MessageCreated": ("MessageMethodsFacade",),
    "MessageEdited": ("MessageMethodsFacade",),
    "MessageRemoved": ("ChatMethodsFacade",),
    "UserAddedToChat": ("ChatMethodsFacade",),
    "UserRemovedFromChat": ("ChatMethodsFacade",),
}

FACADES_MODULE = "maxo.types.facades"


# --- ручные символы в __init__.py -------------------------------------------


@dataclass(slots=True, frozen=True)
class ExtraExport:
    module: str
    names: tuple[str, ...] = field(default_factory=tuple)


#: Алиасы уровня модуля внутри сгенерированного типа: ``Имя: TypeAlias = <Класс>``.
TYPE_ALIASES: dict[str, tuple[tuple[str, str], ...]] = {
    "MessageCallback": (("CallbackQuery", _AIOGRAM),),
}

#: Что дописать в `maxo/types/__init__.py` помимо сгенерированного.
TYPES_EXTRA_EXPORTS: tuple[ExtraExport, ...] = (
    ExtraExport(
        module="base",
        names=(
            "BaseMaxoType",
            "BaseMethodsFacade",
            "BaseUpdate",
            "MaxUpdate",
            "MaxoType",
        ),
    ),
    ExtraExport(
        module="clear_subscriptions_result",
        names=("ClearSubscriptionsResult",),
    ),
    ExtraExport(module="error_event", names=("ErrorEvent",)),
    ExtraExport(module="update_context", names=("UpdateContext",)),
    ExtraExport(module="upload_media_result", names=("UploadMediaResult",)),
)

#: Что дописать в `maxo/bot/methods/__init__.py` - ручные методы и алиасы.
METHODS_EXTRA_EXPORTS: tuple[ExtraExport, ...] = (
    ExtraExport(module="bots.edit_bot_info", names=("EditBotInfo",)),
    ExtraExport(module="chats.delete_admin", names=("DeleteAdmin",)),
    ExtraExport(module="chats.delete_chat", names=("DeleteChat",)),
    ExtraExport(module="chats.get_chat_by_link", names=("GetChatByLink",)),
    ExtraExport(module="chats.get_chats", names=("GetChats",)),
    ExtraExport(module="chats.set_admins", names=("SetAdmins",)),
    ExtraExport(module="upload.upload_media", names=("UploadMedia",)),
)
