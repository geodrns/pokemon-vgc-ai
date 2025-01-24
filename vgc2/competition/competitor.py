from abc import ABC

from vgc2.agent.policies import BattlePolicy, SelectionPolicy, TeamBuildPolicy, MetaBalancePolicy, RuleBalancePolicy
from vgc2.pkm_engine.team import Team


class Competitor(ABC):

    @property
    def battle_policy(self) -> BattlePolicy | None:
        return None

    @property
    def selection_policy(self) -> SelectionPolicy | None:
        return None

    @property
    def team_build_policy(self) -> TeamBuildPolicy | None:
        return None

    @property
    def name(self) -> str:
        return ""


class CompetitorManager:

    def __init__(self,
                 c: Competitor):
        self.competitor: Competitor = c
        self.team: Team | None = None
        self.elo = 1200


class DesignCompetitor(ABC):

    @property
    def meta_balance_policy(self) -> MetaBalancePolicy | None:
        return None

    @property
    def rule_balance_policy(self) -> RuleBalancePolicy | None:
        return None

    @property
    def name(self) -> str:
        return ""
