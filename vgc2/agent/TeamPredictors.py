from typing import Tuple

from vgc2.balance.meta import MetaData

from vgc2.agent import TeamPredictor
from vgc2.datatypes.Objects import PkmFullTeam


class NullTeamPredictor(TeamPredictor):

    def requires_encode(self) -> bool:
        return False

    def close(self):
        pass

    def get_action(self, d: Tuple[PkmFullTeam, MetaData]) -> PkmFullTeam:
        return d[0]
