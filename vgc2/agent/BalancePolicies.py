from typing import Tuple

from vgc2.balance import DeltaRoster
from vgc2.balance.meta import MetaData
from vgc2.balance.restriction import DesignConstraints

from vgc2.agent import BalancePolicy
from vgc2.datatypes.Objects import PkmRoster


class IdleBalancePolicy(BalancePolicy):

    def __init__(self):
        self.dr = DeltaRoster({})

    def requires_encode(self) -> bool:
        return False

    def close(self):
        pass

    def get_action(self, d: Tuple[PkmRoster, MetaData, DesignConstraints]) -> DeltaRoster:
        return self.dr
