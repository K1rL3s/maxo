import inspect
from collections.abc import Callable


def get_callback_params(callback: Callable[..., object]) -> tuple[set[str], bool]:
    """Вернуть имена параметров callback и признак ``**kwargs``."""
    spec = inspect.getfullargspec(callback)
    return {*spec.args, *spec.kwonlyargs}, spec.varkw is not None
