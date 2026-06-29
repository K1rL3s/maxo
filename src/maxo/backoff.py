"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/utils/backoff.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

import asyncio
from dataclasses import dataclass
from random import normalvariate


@dataclass(slots=True, frozen=True)
class BackoffConfig:
    min_delay: float
    max_delay: float
    factor: float
    jitter: float

    def __post_init__(self) -> None:
        if self.max_delay <= self.min_delay:
            raise ValueError("`max_delay` should be greater than `min_delay`")
        if self.factor <= 1:
            raise ValueError("`factor` should be greater than 1")


class Backoff:
    def __init__(self, config: BackoffConfig) -> None:
        self._config = config
        self._current_delay = 0.0
        self._next_delay = config.min_delay
        self._counter = 0

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(tryings={self._counter}, "
            f"current_delay={self._current_delay}, "
            f"next_delay={self._next_delay})"
        )

    @property
    def counter(self) -> int:
        return self._counter

    @property
    def current_delay(self) -> float:
        return self._current_delay

    @property
    def min_delay(self) -> float:
        return self._config.min_delay

    @property
    def max_delay(self) -> float:
        return self._config.max_delay

    @property
    def factor(self) -> float:
        return self._config.factor

    @property
    def jitter(self) -> float:
        return self._config.jitter

    @property
    def next_delay(self) -> float:
        return self._next_delay

    def calc_next_delay(self, current_delay: float) -> float:
        mean = min(current_delay * self.factor, self.max_delay)
        value = normalvariate(mean, self.jitter)
        return min(self.max_delay, max(self.min_delay, value))

    def next(self) -> None:
        self._counter += 1
        self._current_delay = self._next_delay
        self._next_delay = self.calc_next_delay(self._current_delay)

    def reset(self) -> None:
        self._counter = 0
        self._current_delay = 0.0
        self._next_delay = self.min_delay

    async def sleep(self) -> None:
        await asyncio.sleep(self.current_delay)
