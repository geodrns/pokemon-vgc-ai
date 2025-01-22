from abc import abstractmethod, ABC

from vgc2.meta.Restriction import Constraints
from vgc2.meta.meta import Meta
from vgc2.pkm_engine.battle_engine import BattleCommand
from vgc2.pkm_engine.game_state import State
from vgc2.pkm_engine.nature import Nature
from vgc2.pkm_engine.pokemon import PokemonSpecies
from vgc2.pkm_engine.team import Team
from vgc2.pkm_engine.typing import Type

SelectionCommand = list[int]  # indexes on team
TeamBuildCommand = list[tuple[int, tuple[int, ...], tuple[int, ...], Nature, list[int]]]  # id, evs, ivs, nature, moves
RosterBalanceCommand = list[tuple[int, list[Type], tuple[int, ...], list[int]]]  # id, types, stats, moves
RuleBalanceCommand = list[float]  # parameters
Roster = list[PokemonSpecies]


class BattlePolicy(ABC):

    @abstractmethod
    def decision(self, state: State) -> list[BattleCommand]:
        pass


class SelectionPolicy(ABC):

    @abstractmethod
    def decision(self,
                 teams: tuple[Team, Team],
                 max_size: int) -> SelectionCommand:
        pass


class TeamBuildPolicy(ABC):

    @abstractmethod
    def decision(self,
                 roster: Roster,
                 meta: Meta,
                 max_size: int,
                 max_moves: int) -> TeamBuildCommand:
        pass


class MetaBalancePolicy(ABC):

    @abstractmethod
    def decision(self,
                 roster: Roster,
                 meta: Meta,
                 constraints: Constraints) -> RosterBalanceCommand:
        pass


class RuleBalancePolicy(ABC):

    @abstractmethod
    def decision(self,
                 obs: RuleBalanceCommand) -> RuleBalanceCommand:
        pass
