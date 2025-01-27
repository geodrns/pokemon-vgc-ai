from abc import abstractmethod, ABC

from vgc2.battle_engine import BattleCommand
from vgc2.battle_engine.game_state import State
from vgc2.battle_engine.nature import Nature
from vgc2.battle_engine.pokemon import PokemonSpecies
from vgc2.battle_engine.team import Team
from vgc2.battle_engine.typing import Type
from vgc2.meta import Meta
from vgc2.meta.constraints import Constraints

SelectionCommand = list[int]  # indexes on team
TeamBuildCommand = list[tuple[int, tuple[int, ...], tuple[int, ...], Nature, list[int]]]  # id, evs, ivs, nature, moves
RosterBalanceCommand = list[tuple[int, list[Type], tuple[int, ...], list[int]]]  # id, types, stats, moves
RuleBalanceCommand = list[float]  # parameters
Roster = list[PokemonSpecies]


class BattlePolicy(ABC):

    @abstractmethod
    def decision(self,
                 state: State) -> list[BattleCommand]:
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
                 meta: Meta | None,
                 max_team_size: int,
                 max_pkm_moves: int,
                 n_active: int) -> TeamBuildCommand:
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
                 rules: RuleBalanceCommand) -> RuleBalanceCommand:
        pass
