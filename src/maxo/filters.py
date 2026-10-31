"""
Фильтры maxo. Алиас `maxo.routing.filters` для портирования ботов с `aiogram`.

`MagicFilter` и `MagicData` живут в `maxo.integrations.magic_filter`,
потому что `magic_filter` - опциональная зависимость.
"""

from maxo.routing.filters import *  # noqa: F403
