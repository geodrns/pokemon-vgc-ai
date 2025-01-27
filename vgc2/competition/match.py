from typing import Callable

from vgc2.agent import BattlePolicy
from vgc2.battle_engine import BattleEngine
from vgc2.battle_engine.team import Team
from vgc2.battle_engine.view import TeamView
from vgc2.competition import CompetitorManager


def subteam(team: Team,
            view: TeamView,
            idx: list[int]) -> tuple[Team, TeamView]:
    sub_team = Team([team.members[i] for i in idx])
    sub_view = TeamView(team, [view._members[i] for i in idx])
    return sub_team, sub_view


def run_battle(engine: BattleEngine,
               agent: tuple[BattlePolicy, BattlePolicy]) -> int:
    while not engine.finished():
        engine.run_turn((agent[0].decision(engine.state_view[0]), agent[1].decision(engine.state_view[1])))
    return engine.winning_side


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
        engine = BattleEngine(self.n_active)
        while tie or runs < self.n_battles:
            team = self.gen(self.team_size, self.n_moves), self.gen(self.team_size, self.n_moves)
            view = TeamView(team[0]), TeamView(team[1])
            engine.set_teams(team, view)
            self.wins[run_battle(engine, agent)] += 1
            view[0].hide()
            view[1].hide()
            engine.set_teams((team[1], team[0]), (view[1], view[0]))
            self.wins[run_battle(engine, agent)] += 1
            tie = self.wins[0] == self.wins[1]
            runs += 1
        self.finished = True

    def _run_non_random(self):
        agent = self.cm[0].competitor.battle_policy, self.cm[1].competitor.battle_policy
        selector = self.cm[0].competitor.selection_policy, self.cm[1].competitor.selection_policy
        base_team = self.cm[0].team, self.cm[1].team
        base_view = TeamView(base_team[0]), TeamView(base_team[1])
        engine = BattleEngine(self.n_active)
        tie = True
        runs = 0
        while tie or runs < self.n_battles:
            idx = (selector[0].decision((base_team[0], base_view[1]), self.team_size),
                   selector[1].decision((base_team[1], base_view[0]), self.team_size))
            sub = subteam(base_team[0], base_view[0], idx[0]), subteam(base_team[1], base_view[1], idx[1])
            team = sub[0][0], sub[1][0]
            view = sub[0][1], sub[1][1]
            engine.set_teams(team, view)
            self.wins[run_battle(engine, agent)] += 1
            tie = self.wins[0] == self.wins[1]
            runs += 1
        self.finished = True
