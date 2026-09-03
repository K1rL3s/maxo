from maxo.omit import Omittable, Omitted
from maxo.types import MaxoType


class WebhookConfig(MaxoType):
    """Webhook configuration for setWebhook API parameters."""

    update_types: Omittable[list[str]] = Omitted()
