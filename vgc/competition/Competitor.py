from abc import ABC, abstractmethod

from vgc.behaviour import BattlePolicy, TeamSelectionPolicy, TeamBuildPolicy, TeamPredictor, BalancePolicy


class Competitor(ABC):

    @property
    @abstractmethod
    def battle_policy(self) -> BattlePolicy:
        pass

    @property
    @abstractmethod
    def team_selection_policy(self) -> TeamSelectionPolicy:
        pass

    @property
    @abstractmethod
    def team_build_policy(self) -> TeamBuildPolicy:
        pass

    @property
    @abstractmethod
    def team_predictor(self) -> TeamPredictor:
        pass

    @property
    @abstractmethod
    def balance_policy(self) -> BalancePolicy:
        pass

    @property
    def name(self) -> str:
        return ""
