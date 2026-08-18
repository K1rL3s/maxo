"""Тесты формы сгенерированного кода."""

import re
from pathlib import Path

from butcher import emit
from butcher.profile import Enum, Field, MaxoDocument, Method, Model
from butcher.render import docs, enums, fields, inits, methods, types, unions


def _model(document: MaxoDocument, name: str) -> Model:
    return next(item for item in document.models if item.name == name)


def _enum(document: MaxoDocument, name: str) -> Enum:
    return next(item for item in document.enums if item.name == name)


def _method(document: MaxoDocument, name: str) -> Method:
    return next(item for item in document.methods if item.name == name)


def test_model_declares_base_and_tag_default(document: MaxoDocument) -> None:
    source = types.render(_model(document, "PhotoAttachment"))
    assert "class PhotoAttachment(Attachment):" in source
    assert "    type: AttachmentType = AttachmentType.IMAGE" in source
    assert "from maxo.types.attachment import Attachment" in source


def test_update_declares_bare_type_assignment(document: MaxoDocument) -> None:
    source = types.render(_model(document, "MessageCreated"))
    assert "class MessageCreated(MaxUpdate, MessageMethodsFacade):" in source
    assert "    type = UpdateType.MESSAGE_CREATED" in source


def test_model_renders_unsafe_property(document: MaxoDocument) -> None:
    source = types.render(_model(document, "Message"))
    assert "    def unsafe_url(self) -> str:" in source
    assert '            attr="url",' in source


def test_model_docstring_has_args_block(document: MaxoDocument) -> None:
    source = types.render(_model(document, "Message"))
    assert "    Args:" in source
    assert "        timestamp: Время создания сообщения" in source


def test_unsafe_properties_sorted_alphabetically(document: MaxoDocument) -> None:
    # unsafe_*-свойства идут по алфавиту имени поля, а не в порядке объявления.
    source = types.render(_model(document, "Message"))
    order = re.findall(r"def unsafe_(\w+)", source)
    assert order == sorted(order)


def test_enum_renders_extras(document: MaxoDocument) -> None:
    source = enums.render(_enum(document, "AttachmentType"))
    assert 'TEXT = "text"  # Самодельное поле' in source
    assert "    IMAGE = 'image'" in source or '    IMAGE = "image"' in source
    assert "    PHOTO = IMAGE" in source
    assert "ContentType: TypeAlias = AttachmentType  # Подражание aiogram" in source


def test_enum_single_line_description_stays_inline(document: MaxoDocument) -> None:
    source = enums.render(_enum(document, "AttachmentType"))
    assert '    """Вложение"""' in source


def test_method_renders_markers_and_dunders(document: MaxoDocument) -> None:
    source = methods.render(_method(document, "SendMessage"))
    assert "class SendMessage(MaxoMethod[Message]):" in source
    assert '    __url__ = "messages"' in source
    assert '    __method__ = "post"' in source
    assert "    chat_id: Query[Omittable[int]] = Omitted()" in source
    assert "    text: Body[str | None] = None" in source
    assert "    Источник: https://dev.max.ru/docs-api/methods/POST/messages" in source


def test_method_path_placeholder_is_snake_case(document: MaxoDocument) -> None:
    source = methods.render(_method(document, "GetChat"))
    assert '    __url__ = "chats/{chat_id}"' in source
    assert "    chat_id: Path[int]" in source


def test_unions_render_without_blank_lines(document: MaxoDocument) -> None:
    attachments = next(item for item in document.unions if item.module == "attachments")
    source = unions.render(attachments)
    assert "MediaAttachments = PhotoAttachment | VideoAttachment\n" in source
    assert "\n\nAttachments" not in source.split("MediaAttachments", 1)[1]


def test_updates_alias_is_annotated(document: MaxoDocument) -> None:
    updates = next(item for item in document.unions if item.module == "updates")
    source = unions.render(updates)
    assert "from typing import TypeAlias" in source
    assert "Updates: TypeAlias = MessageCreated" in source


def test_init_renders_empty_all_as_tuple() -> None:
    assert inits.render([]) == "\n\n__all__ = ()\n"


def test_emit_uses_project_import_sorting(
    document: MaxoDocument,
    tmp_path: Path,
) -> None:
    emit.write(document, tmp_path)

    source = (tmp_path / "types" / "__init__.py").read_text(encoding="utf-8")
    assert (
        "from .base import BaseMaxoType, BaseUpdate, BotMixin, MaxUpdate, MaxoType"
        in source
    )


def test_links_become_absolute() -> None:
    assert docs.clean("см. [тут](/docs-api#Якорь)") == (
        "см. [тут](https://dev.max.ru/docs-api#Якорь)"
    )
    assert docs.clean("см. [тут](/docs/webapps/bridge)") == (
        "см. [тут](https://dev.max.ru/docs/webapps/bridge)"
    )
    # Абсолютные ссылки не трогаем.
    assert docs.clean("[a](https://example.com)") == "[a](https://example.com)"


def test_dashes_are_normalized() -> None:
    assert docs.clean("а — б – в") == "а - б - в"


def test_br_becomes_newline() -> None:
    assert docs.clean("а<br/>б<br>в</br>г") == "а\nб\nв\nг"


def test_reflow_indents_tight_list() -> None:
    # Плотный список (пункты сразу за вводной) сдвигается вправо на 4.
    text = "Возможные значения:\n- a\n- b"
    assert docs.reflow_lists(text) == "Возможные значения:\n    - a\n    - b"


def test_reflow_leaves_loose_list() -> None:
    # Разреженный список (пустая строка перед пунктами) остаётся как есть.
    text = "Возможные значения:\n\n- a\n\n- b"
    assert docs.reflow_lists(text) == text


def test_reflow_skips_code_fence() -> None:
    # Строки внутри ``` не трогаем: там могут быть флаги curl (`-H`, `-d`).
    text = "```bash\n- H заголовок\n```\n- пункт"
    assert docs.reflow_lists(text) == "```bash\n- H заголовок\n```\n    - пункт"


def test_field_render_includes_trailing_comment() -> None:
    field = Field(
        name="text",
        annotation="str",
        omittable=True,
        comment="type: ignore[assignment]",
    )
    assert fields.render(field)[0] == (
        "    text: Omittable[str] = Omitted()  # type: ignore[assignment]"
    )


def test_reflow_detached_list_stays_aligned() -> None:
    # Оторванный список (пустая строка перед ним) не сдвигаем целиком - иначе
    # первый пункт остаётся на месте, а остальные «съезжают».
    text = "вводная:\n\n- a\n- b\n- c"
    assert docs.reflow_lists(text) == text


def test_collapse_removes_blank_between_items() -> None:
    text = "- a\n\n- b\n\n- c"
    assert docs.collapse_list_blanks(text) == "- a\n- b\n- c"


def test_collapse_removes_blank_before_list() -> None:
    # Пустую строку перед списком убираем - список печатаем плотно за вводной.
    text = "вводная:\n\n- a\n- b"
    assert docs.collapse_list_blanks(text) == "вводная:\n- a\n- b"


def test_collapse_ignores_code_fence() -> None:
    text = "```\n- a\n\n- b\n```"
    assert docs.collapse_list_blanks(text) == text
