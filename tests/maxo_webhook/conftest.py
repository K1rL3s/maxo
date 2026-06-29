from ipaddress import IPv4Address

import pytest

from maxo import Bot


@pytest.fixture
def bot() -> Bot:
    return Bot("42:TEST")


@pytest.fixture
def localhost_ip() -> IPv4Address:
    return IPv4Address("127.0.0.1")
