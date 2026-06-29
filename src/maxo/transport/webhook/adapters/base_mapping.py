from abc import ABC, abstractmethod
from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from typing import Any, Generic, TypeVar

M_co = TypeVar("M_co", bound=Mapping[str, Any], covariant=True)


class MappingABC(ABC, Generic[M_co]):
    def __init__(self, mapping: M_co) -> None:
        self._mapping = mapping

    def get(self, name: str, default: Any = None) -> Any:
        return self._mapping.get(name, default)

    @abstractmethod
    def getlist(self, name: str) -> list[Any]:
        raise NotImplementedError

    def __getitem__(self, name: str) -> Any:
        return self._mapping[name]

    def __contains__(self, name: str) -> bool:
        return name in self._mapping

    def __len__(self) -> int:
        return len(self._mapping)

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)

    def keys(self) -> KeysView[str]:
        return self._mapping.keys()

    def values(self) -> ValuesView[Any]:
        return self._mapping.values()

    def items(self) -> ItemsView[str, Any]:
        return self._mapping.items()
