import importlib

import pytest

from maxo.transport.long_polling import LongPolling


def test_deprecation_warning():
    with pytest.warns(DeprecationWarning, match="`LongPolling` был перенесён"):
        import maxo.utils.long_polling  # noqa: PLC0415

    importlib.reload(maxo.utils.long_polling)


def test_long_polling_is_reexported():
    from maxo.utils.long_polling import (  # noqa: PLC0415
        LongPolling as ReexportedLongPolling,
    )

    assert ReexportedLongPolling is LongPolling
