# ruff: noqa: PLC0415
import importlib

import pytest

from maxo.transport.webhook.security.checks.check import SecurityCheck


def test_deprecation_warning() -> None:
    import maxo.transport.webhook.security.base_check as base_check

    with pytest.warns(
        DeprecationWarning,
        match="был перенесён из `maxo.transport.webhook.security.base_check`",
    ):
        importlib.reload(base_check)


def test_security_check_reexported_from_checks() -> None:
    import maxo.transport.webhook.security.base_check as base_check

    assert base_check.SecurityCheck is SecurityCheck
    assert base_check.__all__ == ("SecurityCheck",)
