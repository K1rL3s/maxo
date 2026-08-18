"""Имена и пути модулей в пакете maxo."""

from unihttp_openapi_generator.ir.naming import to_snake_case

TYPES_PACKAGE = "maxo.types"
ENUMS_PACKAGE = "maxo.enums"


def module_stem(class_name: str) -> str:
    """Имя файла для класса: ``PhotoAttachment`` -> ``photo_attachment``."""
    return to_snake_case(class_name)


def type_module(class_name: str) -> str:
    return f"{TYPES_PACKAGE}.{module_stem(class_name)}"


def enum_module(class_name: str) -> str:
    return f"{ENUMS_PACKAGE}.{module_stem(class_name)}"


def enum_member(value: str) -> str:
    """Имя члена enum: ``inline_keyboard`` -> ``INLINE_KEYBOARD``."""
    return value.upper().replace("-", "_")


def discriminator_enum(base_name: str) -> str:
    """Имя enum из дискриминатора базы: ``Attachment`` -> ``AttachmentType``."""
    return f"{base_name}Type"
