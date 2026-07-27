from collections.abc import MutableMapping
from typing import Any, Final, NewType

Ctx = NewType("Ctx", MutableMapping[str, Any])

CTX_KEY: Final = "ctx"
