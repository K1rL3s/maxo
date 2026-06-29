"""
Что тут происходит.

Класс должен наследоваться от ABC или Protocol для работы @abstractmethod.
но так как MaxoType сделан через метакласс,
то он конфликтует с ABC в моделях апдейтах (миксины всё такое).
Из-за этого фасады и их наследники не наследуются от ABC.

Из-за того, что в BotMixin надо указать __slots__, и без __init__ это не сделать,
и наследование от BaseMethodsFacade и BotMixin одновременно ломает что-то питоновское,
и BaseMethodsFacade по сути определял только пропертю bot,
то BaseMethodsFacade просто стал BotMixin'ом.

И ещё вариант с `class _MaxoTypeABCMeta(_MaxoTypeMetaClass, ABCMeta)`
ломает аннотацию инитов у типов =)

https://github.com/K1rL3s/maxo/pull/103
https://github.com/K1rL3s/maxo/pull/107
"""

from maxo.types import BotMixin

BaseMethodsFacade = BotMixin
