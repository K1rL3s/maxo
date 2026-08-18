"""Общая фикстура-спека для тестов профиля."""

import json
from pathlib import Path
from typing import Any

import pytest

from butcher.profile import MaxoDocument, build_profile
from butcher.spec import load

SPEC: dict[str, Any] = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {
        "/messages": {
            "post": {
                "operationId": "sendMessage",
                "tags": ["messages"],
                "summary": "Отправить сообщение",
                "parameters": [
                    {
                        "name": "chat_id",
                        "in": "query",
                        "description": "ID чата",
                        "schema": {"type": "integer", "format": "int64"},
                    },
                    {
                        "name": "disable_link_preview",
                        "in": "query",
                        "schema": {"type": "boolean", "default": False},
                    },
                    {
                        "name": "from",
                        "description": "Время, начиная с которого нужны сообщения",
                        "in": "query",
                        # Через `$ref`, как в настоящей спеке: формат виден только
                        # после разворачивания `INLINE_ALIASES`.
                        "schema": {"$ref": "#/components/schemas/bigint"},
                    },
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["text"],
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "nullable": True,
                                        "description": "Текст сообщения",
                                    },
                                    "attachments": {
                                        "type": "array",
                                        "nullable": True,
                                        "items": {
                                            "$ref": "#/components/schemas/AttachmentRequest",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                "responses": {
                    "200": {
                        "description": "ok",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Message"},
                            },
                        },
                    },
                },
            },
        },
        "/chats/{chatId}": {
            "get": {
                "operationId": "getChat",
                "tags": ["chats"],
                "parameters": [
                    {
                        "name": "chatId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer", "format": "int64"},
                    },
                ],
                "responses": {"200": {"description": "ok"}},
            },
        },
    },
    "components": {
        "schemas": {
            "bigint": {"type": "integer", "format": "int64"},
            "TextFormat": {"type": "string", "enum": ["html", "markdown"]},
            "Message": {
                "description": "Сообщение",
                "required": ["timestamp"],
                "properties": {
                    "timestamp": {
                        "type": "integer",
                        "format": "int64",
                        "description": "Время создания сообщения",
                    },
                    "seq": {
                        "type": "integer",
                        "format": "int64",
                        "description": "ID последовательности",
                    },
                    "attachments": {
                        "type": "array",
                        "nullable": True,
                        "items": {"$ref": "#/components/schemas/Attachment"},
                    },
                    "url": {"type": "string", "nullable": True},
                    "notify": {
                        "type": "boolean",
                        "default": True,
                        "description": "Уведомлять ли участников",
                    },
                },
            },
            "Attachment": {
                "description": "Вложение",
                "required": ["type"],
                "properties": {"type": {"type": "string"}},
                "discriminator": {
                    "propertyName": "type",
                    "mapping": {
                        "image": "#/components/schemas/PhotoAttachment",
                        "video": "#/components/schemas/VideoAttachment",
                    },
                },
            },
            "PhotoAttachment": {
                "allOf": [
                    {"$ref": "#/components/schemas/Attachment"},
                    {
                        "required": ["payload"],
                        "properties": {"payload": {"type": "string"}},
                    },
                ],
            },
            "VideoAttachment": {"allOf": [{"$ref": "#/components/schemas/Attachment"}]},
            "AttachmentRequest": {
                "required": ["type"],
                "properties": {"type": {"type": "string"}},
                "discriminator": {
                    "propertyName": "type",
                    "mapping": {"image": "#/components/schemas/PhotoAttachmentRequest"},
                },
            },
            "PhotoAttachmentRequest": {
                "allOf": [{"$ref": "#/components/schemas/AttachmentRequest"}],
            },
            "Update": {
                "required": ["update_type", "timestamp"],
                "properties": {
                    "update_type": {"type": "string"},
                    "timestamp": {
                        "type": "integer",
                        "format": "int64",
                        "description": "Unix-время события",
                    },
                },
                "discriminator": {
                    "propertyName": "update_type",
                    "mapping": {
                        "message_created": "#/components/schemas/MessageCreatedUpdate",
                    },
                },
            },
            "MessageCreatedUpdate": {
                "description": "Сообщение создано",
                "allOf": [
                    {"$ref": "#/components/schemas/Update"},
                    {
                        "required": ["message"],
                        "properties": {
                            "message": {"$ref": "#/components/schemas/Message"},
                            "user_locale": {"type": "string", "nullable": True},
                        },
                    },
                ],
            },
            "ChatButton": {"properties": {"kind": {"type": "string"}}},
        },
    },
}


@pytest.fixture(scope="session")
def document(tmp_path_factory: pytest.TempPathFactory) -> MaxoDocument:
    path: Path = tmp_path_factory.mktemp("spec") / "swagger.json"
    path.write_text(json.dumps(SPEC), encoding="utf-8")
    return build_profile(load(str(path)))
