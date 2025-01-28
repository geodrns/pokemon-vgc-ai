from typing import SupportsFloat, Any

from gymnasium import Env
from gymnasium.core import ActType, ObsType, RenderFrame


class BattleEnv(Env):  # TODO Gymnasium

    def __init__(self):
        pass

    def step(self,
             action: ActType) -> tuple[ObsType, SupportsFloat, bool, bool, dict[str, Any]]:
        pass

    def reset(self,
              *,
              seed: int | None = None,
              options: dict[str, Any] | None = None) -> tuple[ObsType, dict[str, Any]]:
        pass

    def render(self) -> RenderFrame | list[RenderFrame] | None:
        pass

    def close(self):
        pass
