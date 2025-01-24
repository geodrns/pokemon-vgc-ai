from random import shuffle

from vgc2.agent.policies import Roster
from vgc2.competition.competitor import CompetitorManager
from vgc2.competition.match import Match
from vgc2.util.generator.team import TeamGenerator, gen_team


class MatchHandler:

    def __init__(self):
        self.prev: tuple | None = None
        self.cm: tuple[CompetitorManager, CompetitorManager] | None = None
        self.winner: CompetitorManager | None = None

    def setup(self, cms):
        if len(cms) == 1:
            self.winner = cms[0]
        elif len(cms) == 2:
            self.cm = cms[0], cms[1]
        else:
            self.prev = MatchHandler(), MatchHandler()
            self.prev[0].setup(cms[:len(cms / 2)])
            self.prev[1].setup(cms[len(cms / 2):])

    def run(self):
        if self.winner is not None:
            return
        if len(self.prev) > 0:
            for mh in self.prev:
                mh.run()
                self.cm += [mh.winner]
        match = Match(self.cm, )
        match.run()
        self.winner = self.cm[match.wins[1] > match.wins[0]]


class TreeChampionship:
    __slots__ = ('cms', 'random_teams', 'roster', 'max_size', 'max_moves', 'gen', 'mh')

    def __init__(self,
                 cms: list[CompetitorManager],
                 roster: Roster | None = None,
                 max_size: int = 4,
                 max_moves: int = 4,
                 gen: TeamGenerator = gen_team):
        self.cms = cms
        self.random_teams = roster is None
        self.roster = roster
        self.max_size = max_size
        self.max_moves = max_moves
        self.gen = gen
        self.mh = MatchHandler()

    def set_teams(self):
        if not self.random_teams:
            for cm in self.cms:
                cm.team = cm.competitor.team_build_policy.decision(self.roster, None, self.max_size,
                                                                   self.max_moves)

    def build_tree(self):
        shuffle(self.cms)
        self.mh.setup(self.cms)

    def run(self):
        self.mh.run()

    def winner(self) -> CompetitorManager:
        return self.mh.winner
