"""Тесты слияния двух публикаций спеки."""

from typing import Any

from butcher.merge import merge_specs

BASE: dict[str, Any] = {
    "paths": {
        "/messages": {
            "get": {
                "operationId": "getMessages",
                "parameters": [
                    {
                        "name": "chat_id",
                        "in": "query",
                        "description": "ID чата",
                        "schema": {"type": "integer"},
                    },
                ],
            },
        },
    },
    "components": {
        "schemas": {
            "SenderAction": {"type": "string", "enum": ["typing_on"]},
            "Message": {
                "description": "Сообщение",
                "required": ["body"],
                "properties": {"sender": {"$ref": "#/components/schemas/User"}},
            },
            "ChatMember": {
                "allOf": [
                    {"$ref": "#/components/schemas/User"},
                    {"properties": {"alias": {"type": "string"}}},
                ],
            },
        },
    },
}

EXTRA: dict[str, Any] = {
    "paths": {
        "/messages": {
            "get": {
                "operationId": "getMessages",
                "parameters": [
                    {
                        "name": "chat_id",
                        "in": "query",
                        "description": "Chat identifier",
                        "schema": {"type": "integer"},
                    },
                    {
                        "name": "after",
                        "in": "query",
                        "schema": {"type": "integer"},
                    },
                ],
            },
        },
        "/videos": {"get": {"operationId": "getVideo"}},
    },
    "components": {
        "schemas": {
            "SenderAction": {"type": "string", "enum": ["typing_on", "mark_seen"]},
            "Message": {
                "description": "Message",
                "required": [],
                "properties": {
                    "sender": {
                        "$ref": "#/components/schemas/User",
                        "nullable": True,
                    },
                    "stat": {"$ref": "#/components/schemas/MessageStat"},
                },
            },
            "ChatMember": {
                "allOf": [
                    {"$ref": "#/components/schemas/User"},
                    {"properties": {"alias": {"type": "string", "nullable": True}}},
                ],
            },
            "MessageStat": {"properties": {"views": {"type": "integer"}}},
        },
    },
}


def test_merge_keeps_base_descriptions_and_required() -> None:
    merged = merge_specs(BASE, EXTRA)
    message = merged["components"]["schemas"]["Message"]
    parameters = merged["paths"]["/messages"]["get"]["parameters"]

    assert message["description"] == "Сообщение"
    assert message["required"] == ["body"]
    assert parameters[0]["description"] == "ID чата"


def test_merge_adds_missing_members() -> None:
    merged = merge_specs(BASE, EXTRA)
    schemas = merged["components"]["schemas"]
    parameters = merged["paths"]["/messages"]["get"]["parameters"]

    assert schemas["SenderAction"]["enum"] == ["typing_on", "mark_seen"]
    assert "stat" in schemas["Message"]["properties"]
    assert "MessageStat" in schemas
    assert "/videos" in merged["paths"]
    assert [item["name"] for item in parameters] == ["chat_id", "after"]


def test_merge_adds_nullable_including_inside_all_of() -> None:
    merged = merge_specs(BASE, EXTRA)
    schemas = merged["components"]["schemas"]

    assert schemas["Message"]["properties"]["sender"]["nullable"] is True
    assert schemas["ChatMember"]["allOf"][1]["properties"]["alias"]["nullable"] is True


def test_merge_keeps_base_when_all_of_shapes_differ() -> None:
    base = {"components": {"schemas": {"ChatMember": {"allOf": [{"type": "object"}]}}}}
    extra = {
        "components": {
            "schemas": {
                "ChatMember": {
                    "allOf": [
                        {"$ref": "#/components/schemas/User"},
                        {"properties": {"alias": {"nullable": True}}},
                    ],
                },
            },
        },
    }

    merged = merge_specs(base, extra)
    chat_member = merged["components"]["schemas"]["ChatMember"]

    assert chat_member["allOf"] == [{"type": "object"}]


def test_merge_does_not_mutate_arguments() -> None:
    merge_specs(BASE, EXTRA)

    assert BASE["components"]["schemas"]["SenderAction"]["enum"] == ["typing_on"]
    assert "stat" not in BASE["components"]["schemas"]["Message"]["properties"]
