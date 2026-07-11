from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)
from typing import Any

from maxo import Bot
from maxo.transport.webhook.adapters.base_adapter import BoundRequest
from maxo.transport.webhook.security.checks.check import SecurityCheck

IPNetwork = IPv4Network | IPv6Network
IPAddress = IPv4Address | IPv6Address


class IPCheck(SecurityCheck):
    """
    Проверка IP-адреса клиента по списку разрешённых адресов и сетей.

    Пропускает запросы только с указанных IP-адресов и подсетей. MAX не
    публикует официальный список IP-адресов, с которых приходят Webhook-запросы,
    поэтому разрешённые адреса и сети необходимо задавать явно.
    """

    def __init__(self, *ip_entries: IPNetwork | IPAddress | str) -> None:
        """
        Инициализировать проверку разрешёнными адресами и сетями.

        :param ip_entries: IP-адреса или подсети, которые нужно разрешить.
        """
        self._networks: set[IPNetwork] = set()
        self._addresses: set[IPAddress] = set()

        for item in ip_entries:
            parsed = self._parse(item)
            if isinstance(parsed, (IPv4Network, IPv6Network)):
                self._networks.add(parsed)
            else:
                self._addresses.add(parsed)

    async def verify(self, bot: Bot, bound_request: BoundRequest[Any]) -> bool:
        raw_ip = self._get_client_ip(bound_request)
        if not raw_ip:
            return False
        try:
            ip_addr = ip_address(raw_ip)
        except ValueError:
            return False
        return ip_addr in self._addresses or any(
            ip_addr in network for network in self._networks
        )

    def _get_client_ip(
        self,
        bound_request: BoundRequest[Any],
    ) -> IPAddress | str | None:
        # Пытаемся получить IP клиента за обратным прокси (X-Forwarded-For).
        forwarded_for = self._extract_first_ip_from_header(
            bound_request.headers.get("X-Forwarded-For"),
        )
        if forwarded_for:
            return forwarded_for

        # Иначе берём IP напрямую из соединения.
        return bound_request.client_ip

    @staticmethod
    def _extract_first_ip_from_header(header_value: str | None) -> str | None:
        """
        Извлечь первый IP из значения заголовка (например, X-Forwarded-For).

        :param header_value: значение заголовка с возможной цепочкой IP.
        :return: первый IP или None.
        """
        if header_value:
            return header_value.split(",", maxsplit=1)[0].strip()
        return None

    @staticmethod
    def _parse(item: IPAddress | IPNetwork | str) -> IPAddress | IPNetwork:
        if isinstance(item, str):
            if "/" in item:
                return ip_network(item, strict=False)
            return ip_address(item)
        return item
