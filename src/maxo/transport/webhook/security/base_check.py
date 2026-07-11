# ruff: noqa: E402

import warnings

warnings.warn(
    "`SecurityCheck` был перенесён из "
    "`maxo.transport.webhook.security.base_check` в "
    "`maxo.transport.webhook.security.checks.check`. "
    "Пожалуйста, обновите импорты на "
    "`from maxo.transport.webhook.security.checks.check import SecurityCheck`.",
    DeprecationWarning,
    stacklevel=2,
)

from maxo.transport.webhook.security.checks.check import SecurityCheck

__all__ = ("SecurityCheck",)
