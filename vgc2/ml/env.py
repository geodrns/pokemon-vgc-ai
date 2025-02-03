from typing import SupportsFloat, Any

from gymnasium import Env
from gymnasium.core import ActType, ObsType, RenderFrame
from gymnasium.spaces import MultiDiscrete, Box
from numpy import zeros

from vgc2.agent import BattlePolicy
from vgc2.agent.battle import RandomBattlePolicy
from vgc2.battle_engine import BattleEngine, Team, TeamView, State, BattlingTeam
from vgc2.util.encoding import encode_state, EncodeContext
from vgc2.util.generator import gen_team


def obs_encode_len(n_active: int,
                   max_team_size: int,
                   max_pkm_moves: int) -> int:
    state = State()
    team = gen_team(max_team_size, max_pkm_moves)
    b_team = BattlingTeam(team.members[:n_active], team.members[n_active:])
    state.sides[0].team = b_team
    state.sides[1].team = b_team
    e = zeros(10000)
    return encode_state(e, state, EncodeContext())


class BattleEnv(Env):

    def __init__(self,
                 ctx: EncodeContext,
                 n_active: int = 2,
                 max_team_size: int = 4,
                 max_pkm_moves: int = 4):
        encode_len = obs_encode_len(n_active, max_team_size, max_pkm_moves)
        self.ctx = ctx
        self.n_active = n_active
        self.action_space = MultiDiscrete([max_pkm_moves + 1, max(max_team_size - n_active, n_active)] * n_active,
                                          start=[-1, 0] * n_active)
        self.observation_space = Box(-1., 1., (1, encode_len))  # TODO gym define obs limits per dim
        self.opponent = RandomBattlePolicy()
        self.engine = BattleEngine(n_active)
        self.encode_buffer = zeros(encode_len)

    def set_opponent(self, opponent: BattlePolicy):
        self.opponent = opponent

    def set_teams(self,
                  teams: tuple[Team, Team],
                  views: tuple[TeamView, TeamView]):
        self.engine.set_teams(teams, views)

    def step(self,
             action: ActType) -> tuple[ObsType, SupportsFloat, bool, bool, dict[str, Any]]:
        opp_action = self.opponent.decision(self.engine.state_view[1])
        self.engine.run_turn(([(int(action[i * 2]), int(action[i * 2 + 1])) for i in range(self.n_active)], opp_action))
        terminated = self.engine.state.terminal()
        truncated = False
        reward = float(self.engine.winning_side == 0)  # the agent is only reached at the end of the episode
        observation = self._get_obs()
        info = self._get_info()
        return observation, reward, terminated, truncated, info

    def reset(self,
              *,
              seed: int | None = None,
              options: dict[str, Any] | None = None) -> tuple[ObsType, dict[str, Any]]:
        self.engine.reset()
        observation = self._get_obs()
        info = self._get_info()
        return observation, info

    def render(self) -> RenderFrame | list[RenderFrame] | None:
        pass

    def close(self):
        pass

    def _get_obs(self):
        encode_state(self.encode_buffer, self.engine.state_view[0], self.ctx)
        return self.encode_buffer

    def _get_info(self):
        return {}
