from typing import Callable


class Meta:
    pass


MetaEvaluator = Callable[[Meta], float]


def evaluate_meta(meta: Meta) -> float:
    return 0.
