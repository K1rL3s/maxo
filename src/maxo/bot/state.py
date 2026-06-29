from abc import abstractmethod
from typing import Protocol

from maxo.bot.api_client import MaxApiClient
from maxo.errors.state import StateError
from maxo.types.bot_info import BotInfo


class BotState(Protocol):
    __slots__ = ()

    @property
    @abstractmethod
    def api_client(self) -> MaxApiClient:
        raise NotImplementedError

    @property
    @abstractmethod
    def started(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def closed(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def info(self) -> BotInfo:
        raise NotImplementedError


class EmptyBotState(BotState):
    __slots__ = ()

    @property
    def api_client(self) -> MaxApiClient:
        raise StateError("Not started bot")

    @property
    def started(self) -> bool:
        return False

    @property
    def closed(self) -> bool:
        return False

    @property
    def info(self) -> BotInfo:
        raise StateError("Not started bot")


class ClosedBotState(BotState):
    __slots__ = ()

    @property
    def api_client(self) -> MaxApiClient:
        raise StateError("Bot closed")

    @property
    def started(self) -> bool:
        return False

    @property
    def closed(self) -> bool:
        return True

    @property
    def info(self) -> BotInfo:
        raise StateError("Bot closed")


class ConnectingBotState(BotState):
    __slots__ = ("_api_client",)

    def __init__(self, api_client: MaxApiClient) -> None:
        self._api_client = api_client

    @property
    def api_client(self) -> MaxApiClient:
        return self._api_client

    @property
    def started(self) -> bool:
        return True

    @property
    def closed(self) -> bool:
        return False

    @property
    def info(self) -> BotInfo:
        raise StateError("Bot is connecting")


class RunningBotState(ConnectingBotState):
    __slots__ = ("_info",)

    def __init__(
        self,
        info: BotInfo,
        api_client: MaxApiClient,
    ) -> None:
        super().__init__(api_client=api_client)
        self._info = info

    @property
    def info(self) -> BotInfo:
        return self._info
