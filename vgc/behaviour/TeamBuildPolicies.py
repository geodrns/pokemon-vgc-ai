import random
from copy import deepcopy
from typing import List, Tuple

import numpy as np

from vgc.balance.meta import MetaData
from vgc.behaviour import TeamBuildPolicy
from vgc.behaviour.BattlePolicies import Minimax
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_TEAM_SIZE
from vgc.datatypes.Objects import Pkm, PkmTemplate, PkmFullTeam, PkmRoster, PkmTeam
from vgc.engine.PkmBattleEnv import PkmBattleEnv


class RandomTeamBuildPolicy(TeamBuildPolicy):
    """
    Agents that selects teams randomly.
    """

    def requires_encode(self) -> bool:
        return False

    def close(self):
        pass

    def pre_processing(self, roster: PkmRoster):
        pass

    def get_action(self, d: Tuple[MetaData, PkmRoster]) -> PkmFullTeam:
        roster = list(d[1])
        pre_selection: List[PkmTemplate] = [roster[i] for i in random.sample(range(len(roster)), DEFAULT_TEAM_SIZE)]
        team: List[Pkm] = []
        for pt in pre_selection:
            team.append(pt.gen_pkm(random.sample(range(len(pt.move_roster)), DEFAULT_PKM_N_MOVES)))
        return PkmFullTeam(team)


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


class IndividualPkmCounter(TeamBuildPolicy):
    """
    Counter the team composition we believe will be selected by an opponent. We disregard synergies in teams as in the
    original algorithms which were tested over Pokemon GO and look for individual pairwise win rates and coverage.
    Contrary to the source paper, the meta is not the win rate directly but instead the usage rate, which we assume is
    a direct implication of the win rate. We use epistemic reasoning to find the meta counter teams and play in an
    unpredictable fashion.
    Source: https://ieee-cog.org/2021/assets/papers/paper_192.pdf
    """

    def __init__(self):
        self.matchup_table = None
        self.agent0 = Minimax()
        self.agent1 = Minimax()
        self.pkms = []

    def requires_encode(self) -> bool:
        return False

    def close(self):
        pass

    def pre_processing(self, roster: PkmRoster):
        self.pkms = []
        for pt in roster:
            self.pkms.append(pt.gen_pkm([0, 1, 2, 3]))
        n_pkms = len(roster)
        self.matchup_table = np.zeros((n_pkms, n_pkms))
        for i, p0 in enumerate(self.pkms):
            for j, p1 in enumerate(self.pkms[i:]):
                if j == 0:  # p0 == p1
                    self.matchup_table[i][i] = 0.5
                else:
                    wins = [0, 0]
                    t0 = PkmTeam([p0])
                    t1 = PkmTeam([p1])
                    env = PkmBattleEnv((t0, t1), encode=(self.agent0.requires_encode(), self.agent1.requires_encode()))
                    for _ in range(10):
                        s = env.reset()
                        t = False
                        while not t:
                            a0 = self.agent0.get_action(s[0])
                            a1 = self.agent1.get_action(s[1])
                            s, _, t, _ = env.step([a0, a1])
                        wins[env.winner] += 1
                    w0 = wins[0] / 10.0
                    self.matchup_table[i][i + j] = w0
                    self.matchup_table[i + j][i] = 1.0 - w0

    def get_action(self, d: Tuple[MetaData, PkmRoster]) -> PkmFullTeam:
        selected: List[int] = []
        n_pkms = len(self.pkms)
        matchup_table = deepcopy(self.matchup_table)
        meta = np.array([1.0] * n_pkms)
        policy = softmax(np.cross(matchup_table, meta))
        p0 = np.random.choice(n_pkms, p=policy)
        selected.append(p0)
        for i in range(n_pkms):
            matchup_table[p0][i] = 0.
        policy = softmax(np.cross(matchup_table, meta))
        p1 = np.random.choice(n_pkms, p=policy)
        selected.append(p1)
        for i in range(n_pkms):
            matchup_table[p1][i] = 0.
        policy = softmax(np.cross(matchup_table, meta))
        p2 = np.random.choice(n_pkms, p=policy)
        selected.append(p2)
        return PkmFullTeam([self.pkms[selected[0]], self.pkms[selected[1]], self.pkms[selected[2]]])
