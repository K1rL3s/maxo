from ipaddress import IPv4Address, IPv4Network

import pytest

from maxo import Bot
from maxo.transport.webhook.security import IPCheck

from .fixtures import DummyBoundRequest, DummyRequest


@pytest.mark.parametrize(
    ("entries", "client_ip", "expected"),
    [
        # Точный адрес
        (["127.0.0.1"], "127.0.0.1", True),
        (["127.0.0.1"], "127.0.0.2", False),
        # Подсеть
        (["10.0.0.0/8"], "10.1.2.3", True),
        (["10.0.0.0/8"], "11.0.0.1", False),
        # IPv6
        (["::1"], "::1", True),
        # Несколько записей
        (["127.0.0.1", "192.168.0.0/16"], "192.168.1.1", True),
        # Пустой список - никого не пропускаем
        ([], "127.0.0.1", False),
    ],
    ids=[
        "exact-match",
        "exact-mismatch",
        "network-match",
        "network-mismatch",
        "ipv6-match",
        "multiple-entries",
        "empty-denies-all",
    ],
)
async def test_ip_check_client_ip(
    entries: list[str],
    client_ip: str,
    expected: bool,
    bot: Bot,
) -> None:
    check = IPCheck(*entries)
    req = DummyBoundRequest(DummyRequest(ip=client_ip))
    assert await check.verify(bot, req) is expected


async def test_ip_check_no_ip_denies(bot: Bot) -> None:
    check = IPCheck("127.0.0.1")
    req = DummyBoundRequest(DummyRequest(ip=None))
    assert await check.verify(bot, req) is False


async def test_ip_check_invalid_ip_denies(bot: Bot) -> None:
    check = IPCheck("127.0.0.1")
    req = DummyBoundRequest(DummyRequest(ip="not-an-ip"))
    assert await check.verify(bot, req) is False


async def test_ip_check_uses_x_forwarded_for(bot: Bot) -> None:
    check = IPCheck("203.0.113.7")
    req = DummyBoundRequest(
        DummyRequest(
            ip="10.0.0.1",
            headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"},
        ),
    )
    assert await check.verify(bot, req) is True


async def test_ip_check_x_forwarded_for_takes_priority_over_client_ip(
    bot: Bot,
) -> None:
    # X-Forwarded-For содержит неразрешённый IP, хотя прямое соединение - разрешено.
    check = IPCheck("10.0.0.1")
    req = DummyBoundRequest(
        DummyRequest(
            ip="10.0.0.1",
            headers={"X-Forwarded-For": "203.0.113.7"},
        ),
    )
    assert await check.verify(bot, req) is False


def test_ip_check_accepts_parsed_objects(bot: Bot) -> None:
    check = IPCheck(IPv4Address("127.0.0.1"), IPv4Network("10.0.0.0/8"))
    assert IPv4Address("127.0.0.1") in check._addresses
    assert IPv4Network("10.0.0.0/8") in check._networks
