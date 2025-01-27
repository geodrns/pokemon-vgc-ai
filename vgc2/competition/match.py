from typing import Callable

from vgc2.agent import BattlePolicy
from vgc2.battle_engine import BattleEngine
from vgc2.battle_engine.team import Team
from vgc2.battle_engine.view import TeamView, StateView
from vgc2.competition import CompetitorManager


class Match:

    def __init__(self,
                 cm: tuple[CompetitorManager, CompetitorManager],
                 n_active: int = 2,
                 n_battles: int = 3,
                 team_size: int = 4,
                 n_moves: int = 4,
                 random_teams: bool = False,
                 gen: Callable[[int, int], Team] | None = None):
        self.cm = cm
        self.n_active = n_active
        self.n_battles = n_battles
        self.team_size = team_size
        self.n_moves = n_moves
        self.random_teams = random_teams
        self.gen = gen
        self.wins = [0, 0]

    def run(self):
        if self.random_teams:
            self._run_random()
        else:
            self._run_non_random()

    def _run_random(self):
        agent = self.cm[0].competitor.battle_policy, self.cm[1].competitor.battle_policy
        tie = True
        runs = 0
        while tie or runs < self.n_battles:
            team = self.gen(self.team_size, self.n_moves), self.gen(self.team_size, self.n_moves)
            self.wins[self._run_battle(agent, team)] += 1
            self.wins[self._run_battle(agent, (team[1], team[0]))] += 1
            tie = self.wins[0] == self.wins[1]
            runs += 1
        self.finished = True

    def _run_non_random(self):
        agent = self.cm[0].competitor.battle_policy, self.cm[1].competitor.battle_policy
        selector = self.cm[0].competitor.selection_policy, self.cm[1].competitor.selection_policy
        base_team = self.cm[0].team, self.cm[1].team
        view = TeamView(base_team[0]), TeamView(base_team[1])
        tie = True
        runs = 0
        while tie or runs < self.n_battles:
            team = (base_team[0].subteam(selector[0].decision((base_team[0], view[1]), self.team_size)),
                    base_team[1].subteam(selector[1].decision((base_team[1], view[0]), self.team_size)))
            self.wins[self._run_battle(agent, team)] += 1
            self.wins[self._run_battle(agent, (team[1], team[0]))] += 1
            tie = self.wins[0] == self.wins[1]
            runs += 1
        self.finished = True

    def _run_battle(self,
                    agent: tuple[BattlePolicy, BattlePolicy],
                    team: tuple[Team, Team]) -> int:
        engine = BattleEngine(team, self.n_active)
        view = StateView(engine.state, 0), StateView(engine.state, 1)
        while not engine.finished():
            engine.run_turn((agent[0].decision(view[0]), agent[1].decision(view[1])))
        return engine.winning_side
