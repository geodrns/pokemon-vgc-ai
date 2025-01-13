from typing import List, Tuple

from gymnasium import Env

from vgc.pkm_engine.game_state import State, Side
from vgc.pkm_engine.pokemon import Pokemon, BattlingPokemon

Team = List[Pokemon]
BattlingTeam = List[BattlingPokemon]


def battling_team(team: Team):
    return [BattlingPokemon(p) for p in team]


class BattleEngine:

    def __init__(self, teams: Tuple[Team, Team], n_active: int = 1):
        battling_teams = (battling_team(teams[0]), battling_team(teams[1]))
        self.n_active = n_active
        self.state = State((
            Side(
                battling_teams[0][:self.n_active],
                battling_teams[0][self.n_active:]
            ),
            Side(
                battling_teams[1][:self.n_active],
                battling_teams[1][self.n_active:]
            )
        ))

    def reset(self):
        self.state.reset()

    def change_teams(self, teams: Tuple[Team, Team]):
        battling_teams = (battling_team(teams[0]), battling_team(teams[1]))
        self.state.sides[0].active = battling_teams[0][:self.n_active]
        self.state.sides[0].reserve = battling_teams[0][self.n_active:]
        self.state.sides[1].active = battling_teams[1][:self.n_active]
        self.state.sides[1].reserve = battling_teams[1][self.n_active:]

    def run_turn(self):
        pass


class BattleEnv(Env, BattleEngine):
    def __init__(self):
        super().__init__()
