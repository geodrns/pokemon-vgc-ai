import random
from typing import List, Tuple, Optional

from vgc.balance.meta import MetaData
from vgc.behaviour import TeamBuildPolicy
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, DEFAULT_TEAM_SIZE
from vgc.datatypes.Objects import Pkm, PkmTemplate, PkmFullTeam, PkmRoster


class RandomTeamBuildPolicy(TeamBuildPolicy):

    def close(self):
        pass

    def get_action(self, d: Tuple[MetaData, Optional[PkmFullTeam], PkmRoster]) -> PkmFullTeam:
        roster = list(d[2])
        pre_selection: List[PkmTemplate] = [roster[i] for i in random.sample(range(len(roster)), DEFAULT_TEAM_SIZE)]
        team: List[Pkm] = []
        for pt in pre_selection:
            team.append(pt.gen_pkm(random.sample(range(len(pt.move_roster)), DEFAULT_PKM_N_MOVES)))
        return PkmFullTeam(team)
