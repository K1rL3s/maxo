from adaptix import Provider
from adaptix._internal.provider.provider_wrapper import ConcatProvider


def concat_provider(*providers: Provider) -> Provider:
    return ConcatProvider(*providers)
