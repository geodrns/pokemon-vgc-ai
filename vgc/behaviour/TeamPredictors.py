from typing import Tuple

from vgc.balance.meta import MetaData
from vgc.behaviour import TeamPredictor
from vgc.datatypes.Objects import PkmTeam


class NullTeamPredictor(TeamPredictor):
    null_team_prediction = PkmTeam()

    def close(self):
        pass

    def get_action(self, d: Tuple[PkmTeam, MetaData]) -> PkmTeam:
        return NullTeamPredictor.null_team_prediction
