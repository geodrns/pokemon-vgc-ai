from random import shuffle

from vgc2.agent import Roster
from vgc2.competition import CompetitorManager
from vgc2.competition.match import Match
from vgc2.util.generator import TeamGenerator, gen_team


class MatchHandler:
    __slots__ = ('max_team_size', 'max_pkm_moves', 'n_active', 'n_battles', 'random_teams', 'gen', 'prev', 'cm',
                 'winner')

    def __init__(self,
                 max_team_size: int = 4,
                 max_pkm_moves: int = 4,
                 n_active: int = 2,
                 n_battles: int = 10,
                 random_teams: bool = True,
                 gen: TeamGenerator = gen_team):
        self.max_team_size = max_team_size
        self.max_pkm_moves = max_pkm_moves
        self.n_active = n_active
        self.n_battles = n_battles
        self.random_teams = random_teams
        self.gen = gen
        self.prev: tuple | None = None
        self.cm: tuple[CompetitorManager, CompetitorManager] | None = None
        self.winner: CompetitorManager | None = None

    def setup(self, cms):
        if len(cms) == 1:
            self.winner = cms[0]
        elif len(cms) == 2:
            self.cm = cms[0], cms[1]
        else:
            self.prev = (MatchHandler(self.max_team_size, self.max_pkm_moves, self.n_active, self.n_battles,
                                      self.random_teams, self.gen),
                         MatchHandler(self.max_team_size, self.max_pkm_moves, self.n_active, self.n_battles,
                                      self.random_teams, self.gen))
            self.prev[0].setup(cms[:len(cms / 2)])
            self.prev[1].setup(cms[len(cms / 2):])

    def run(self):
        if self.winner is not None:
            return
        if len(self.prev) > 0:
            for mh in self.prev:
                mh.run()
                self.cm += [mh.winner]
        match = Match(self.cm, self.n_active, self.n_battles, self.max_team_size, self.max_pkm_moves, self.random_teams,
                      self.gen)
        match.run()
        self.winner = self.cm[match.wins[1] > match.wins[0]]


class TreeTournament:
    __slots__ = ('cms', 'random_teams', 'roster', 'max_team_size', 'max_pkm_moves', 'gen', 'n_active', 'n_battles',
                 'mh')

    def __init__(self,
                 cms: list[CompetitorManager],
                 roster: Roster | None = None,
                 max_team_size: int = 4,
                 max_pkm_moves: int = 4,
                 n_active: int = 2,
                 n_battles: int = 10,
                 gen: TeamGenerator = gen_team):
        self.cms = cms
        self.random_teams = roster is None
        self.roster = roster
        self.max_team_size = max_team_size
        self.max_pkm_moves = max_pkm_moves
        self.n_active = n_active
        self.mh = MatchHandler(max_team_size, max_pkm_moves, n_active, n_battles, self.random_teams, gen)

    def set_teams(self):
        if not self.random_teams:
            for cm in self.cms:
                cm.team = cm.competitor.team_build_policy.decision(self.roster, None, self.max_team_size,
                                                                   self.max_pkm_moves, self.n_active)

    def build_tree(self):
        shuffle(self.cms)
        self.mh.setup(self.cms)

    def run(self) -> CompetitorManager:
        self.mh.run()
        return self.mh.winner
