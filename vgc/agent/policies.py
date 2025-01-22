from abc import abstractmethod, ABC

from numpy import array

from vgc.balance.meta import History
from vgc.balance.restriction import Constraints
from vgc.pkm_engine.battle_engine import BattleCommand
from vgc.pkm_engine.game_state import State
from vgc.pkm_engine.nature import Nature
from vgc.pkm_engine.pokemon import PokemonSpecies
from vgc.pkm_engine.team import Team
from vgc.pkm_engine.typing import Type

SelectionCommand = list[int]  # indexes on team
TeamBuildCommand = list[tuple[int, tuple[int, ...], tuple[int, ...], Nature]]  # id, evs, ivs, nature
RosterBalanceCommand = list[tuple[int, list[Type], tuple[int, ...], list[int]]]  # id, types, stats, move ids
RuleBalanceCommand = list[float]  # parameters
Roster = list[PokemonSpecies]


class BattlePolicy(ABC):

    @abstractmethod
    def decision(self, obs: array | State) -> list[BattleCommand]:
        pass


class SelectionPolicy(ABC):

    @abstractmethod
    def decision(self, obs: tuple[Team, Team]) -> SelectionCommand:
        pass


class TeamBuildPolicy(ABC):

    @abstractmethod
    def decision(self, obs: tuple[Roster, History]) -> TeamBuildCommand:
        pass


class MetaBalancePolicy(ABC):

    @abstractmethod
    def decision(self, obs: tuple[Roster, History, Constraints]) -> RosterBalanceCommand:
        pass


class RuleBalancePolicy(ABC):

    @abstractmethod
    def decision(self, obs: RuleBalanceCommand) -> RuleBalanceCommand:
        pass
