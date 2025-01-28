from vgc2.agent import BattlePolicy
from vgc2.battle_engine import BattleEngine
from vgc2.battle_engine.team import Team
from vgc2.battle_engine.view import TeamView
from vgc2.competition import CompetitorManager
from vgc2.util.generator import TeamGenerator, _rng


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
    __slots__ = ('cm', 'n_active', 'n_battles', 'max_team_size', 'max_pkm_moves', 'random_teams', 'gen', 'wins')

    def __init__(self,
                 cm: tuple[CompetitorManager, CompetitorManager],
                 n_active: int = 2,
                 n_battles: int = 3,
                 max_team_size: int = 4,
                 max_pkm_moves: int = 4,
                 random_teams: bool = True,
                 gen: TeamGenerator | None = None):
        self.cm = cm
        self.n_active = n_active
        self.n_battles = n_battles
        self.max_team_size = max_team_size
        self.max_pkm_moves = max_pkm_moves
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
            team = (self.gen(self.max_team_size, self.max_pkm_moves, _rng),
                    self.gen(self.max_team_size, self.max_pkm_moves, _rng))
            view = TeamView(team[0]), TeamView(team[1])
            engine.set_teams(team, view)
            self.wins[run_battle(engine, agent)] += 1
            view[0].hide()
            view[1].hide()
            engine.set_teams((team[1], team[0]), (view[1], view[0]))
            self.wins[run_battle(engine, agent)] += 1
            tie = self.wins[0] == self.wins[1]
            runs += 1

    def _run_non_random(self):
        agent = self.cm[0].competitor.battle_policy, self.cm[1].competitor.battle_policy
        selector = self.cm[0].competitor.selection_policy, self.cm[1].competitor.selection_policy
        base_team = self.cm[0].team, self.cm[1].team
        base_view = TeamView(base_team[0]), TeamView(base_team[1])
        engine = BattleEngine(self.n_active)
        tie = True
        runs = 0
        while tie or runs < self.n_battles:
            idx = (selector[0].decision((base_team[0], base_view[1]), self.max_team_size),
                   selector[1].decision((base_team[1], base_view[0]), self.max_team_size))
            sub = subteam(base_team[0], base_view[0], idx[0]), subteam(base_team[1], base_view[1], idx[1])
            team = sub[0][0], sub[1][0]
            view = sub[0][1], sub[1][1]
            engine.set_teams(team, view)
            self.wins[run_battle(engine, agent)] += 1
            tie = self.wins[0] == self.wins[1]
            runs += 1
