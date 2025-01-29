from abc import ABC, abstractmethod

from vgc2.battle_engine import Team, Move
from vgc2.battle_engine.pokemon import PokemonSpecies

Roster = list[PokemonSpecies]


class Meta(ABC):
    @abstractmethod
    def add_match(self,
                  team: tuple[Team, Team],
                  elo: tuple[int, int]):
        pass

    @abstractmethod
    def change_roster(self, roster: Roster):
        pass

    @abstractmethod
    def usage_rate_move(self,
                        move: Move) -> float:
        pass

    @abstractmethod
    def usage_rate_pokemon(self,
                           pokemon: PokemonSpecies) -> float:
        pass

    @abstractmethod
    def usage_rate_team(self,
                        team: Team) -> float:
        pass


class StandardMeta(Meta):
    def __init__(self):
        pass
    
    def add_match(self, team: tuple[Team, Team], elo: tuple[int, int]):
        pass

    def change_roster(self, roster: Roster):
        pass

    def usage_rate_move(self, move: Move) -> float:
        pass

    def usage_rate_pokemon(self, pokemon: PokemonSpecies) -> float:
        pass

    def usage_rate_team(self, team: Team) -> float:
        pass
