from typing import List, Tuple

from gymnasium import Env

from vgc.pkm_engine.game_state import State, Side
from vgc.pkm_engine.pokemon import Pokemon, BattlingPokemon

Team = List[Pokemon]
BattlingTeam = List[BattlingPokemon]


def battling_team(team: Team):
    return [BattlingPokemon(p) for p in team]


Action = Tuple[int, int]  # move, target


class BattleEngine:
    __slots__ = ('n_active', 'state')

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

    def __str__(self):
        return str(self.state)

    def reset(self):
        self.state.reset()

    def change_teams(self,
                     teams: Tuple[Team, Team]):
        battling_teams = (battling_team(teams[0]), battling_team(teams[1]))
        self.state.sides[0].active = battling_teams[0][:self.n_active]
        self.state.sides[0].reserve = battling_teams[0][self.n_active:]
        self.state.sides[1].active = battling_teams[1][:self.n_active]
        self.state.sides[1].reserve = battling_teams[1][self.n_active:]

    def run_turn(self,
                 actions: Tuple[List[Action], List[Action]]):
        self._perform_switches(actions)

    def _perform_switches(self,
                          actions: Tuple[List[Action], List[Action]]):
        switches = []
        for i, s in enumerate(actions):
            for j, a in enumerate(s):
                if a[0] == -1:
                    switches += [(i, j, a[1])]
        while len(switches) < 0:
            s, act, rsv = switches.pop()
            self.state.sides[s].switch(act, rsv)
            # hazard damage and add forced switch

    def _perform_moves(self,
                       actions: Tuple[List[int], List[int]]):
        pass


class BattleEnv(Env, BattleEngine):
    def __init__(self):
        super().__init__()
