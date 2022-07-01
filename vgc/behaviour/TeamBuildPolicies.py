import random
from copy import deepcopy
from typing import List

import numpy as np

from vgc.balance.meta import MetaData
from vgc.behaviour import TeamBuildPolicy, BattlePolicy
from vgc.behaviour.BattlePolicies import TypeSelector
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_TEAM_SIZE
from vgc.datatypes.Objects import Pkm, PkmTemplate, PkmFullTeam, PkmRoster, PkmTeam
from vgc.engine.PkmBattleEnv import PkmBattleEnv


class RandomTeamBuilder(TeamBuildPolicy):
    """
    Agents that selects teams randomly.
    """

    def __init__(self):
        self.roster = None

    def requires_encode(self) -> bool:
        return False

    def close(self):
        pass

    def set_roster(self, roster: PkmRoster):
        self.roster = roster

    def get_action(self, meta: MetaData) -> PkmFullTeam:
        roster = list(self.roster)
        pre_selection: List[PkmTemplate] = [roster[i] for i in random.sample(range(len(roster)), DEFAULT_TEAM_SIZE)]
        team: List[Pkm] = []
        for pt in pre_selection:
            team.append(pt.gen_pkm(random.sample(range(len(pt.move_roster)), DEFAULT_PKM_N_MOVES)))
        return PkmFullTeam(team)


def run_battles(pkm0, pkm1, agent0, agent1, n_battles):
    wins = [0, 0]
    t0 = PkmTeam([pkm0])
    t1 = PkmTeam([pkm1])
    env = PkmBattleEnv((t0, t1), encode=(agent0.requires_encode(), agent1.requires_encode()))
    for _ in range(n_battles):
        s = env.reset()
        t = False
        while not t:
            a0 = agent0.get_action(s[0])
            a1 = agent1.get_action(s[1])
            s, _, t, _ = env.step([a0, a1])
        wins[env.winner] += 1
    return wins


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


def select_next(matchup_table, n_pkms, members):
    average_winrate = np.sum(matchup_table, axis=1) / n_pkms
    policy = softmax(average_winrate)
    p = np.random.choice(n_pkms, p=softmax(average_winrate))
    while p in members:
        p = np.random.choice(n_pkms, p=policy)
    members.append(p)
    if len(members) < 3:
        for i in range(n_pkms):
            matchup_table[p][i] = 0.
        select_next(matchup_table, n_pkms, members)


class IndividualPkmCounter(TeamBuildPolicy):
    """
    Counter the team composition we believe will be selected by an opponent. We disregard synergies in teams as in the
    original algorithms which were tested over pkm GO and look for individual pairwise win rates and coverage.
    Contrary to the source paper, the meta is not the win rate directly but instead the usage rate, which we assume is
    a direct implication of the win rate. We use epistemic reasoning to find the meta counter teams and play in an
    unpredictable fashion.
    Source: https://ieee-cog.org/2021/assets/papers/paper_192.pdf
    """

    def __init__(self, agent0: BattlePolicy = TypeSelector(), agent1: BattlePolicy = TypeSelector(), n_battles=10):
        self.matchup_table = None
        self.agent0 = agent0
        self.agent1 = agent1
        self.n_battles = n_battles
        self.pkms = None
        self.n_pkms = -1

    def requires_encode(self) -> bool:
        return False

    def close(self):
        pass

    def set_roster(self, roster: PkmRoster):
        """
        Instead of storing the roster, we fill a pairwise match up table where each entry has the estimated win rate
        from a row pkm against a column pkm.
        """
        self.pkms = []
        for pt in roster:
            self.pkms.append(pt.gen_pkm([0, 1, 2, 3]))
        self.n_pkms = len(roster)
        self.matchup_table = np.zeros((self.n_pkms, self.n_pkms))
        for i, pkm0 in enumerate(self.pkms):
            for j, pkm1 in enumerate(self.pkms[i:]):
                if j == 0:  # p0 == p1
                    self.matchup_table[i][i] = 0.5
                else:
                    wins = run_battles(pkm0, pkm1, self.agent0, self.agent1, self.n_battles)
                    self.matchup_table[i][i + j] = wins[0] / self.n_battles
                    self.matchup_table[i + j][i] = wins[1] / self.n_battles

    def get_action(self, meta: MetaData) -> PkmFullTeam:
        members: List[int] = []
        matchup_table = deepcopy(self.matchup_table)
        select_next(matchup_table, self.n_pkms, members)
        return PkmFullTeam([self.pkms[members[0]], self.pkms[members[1]], self.pkms[members[2]]])
