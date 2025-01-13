import math
from typing import List

from vgc.pkm_engine.constants import NATURES
from vgc.pkm_engine.modifiers import PermStat, Status, Stats
from vgc.pkm_engine.move import Move, BattlingMove
from vgc.pkm_engine.nature import Nature
from vgc.pkm_engine.typing import Type


class PokemonSpecies:
    __slots__ = ('id', 'base_stats', 'types')

    def __init__(self,
                 base_stats: Stats,
                 types: List[Type]):
        self.id = -1
        self.base_stats = base_stats
        self.types = types

    def __str__(self):
        return "Base Stats " + str(self.base_stats) + ", Types " + str([t.name for t in self.types])


def update_stats_from_nature(stats: List[int],
                             nature: Nature):
    new_stats = stats.copy()
    try:
        new_stats[NATURES[nature]['plus']] *= 1.1
        new_stats[NATURES[nature]['minus']] /= 1.1
    except KeyError:
        pass
    return new_stats


def calculate_stat(stat: int,
                   iv: int,
                   ev: int,
                   level: int) -> float:
    return math.floor(((2 * stat + iv + math.floor(ev / 4)) * level) / 100)


def calculate_stats(base_stats: Stats,
                    level: int,
                    ivs: Stats = (31,) * 6,
                    evs: Stats = (85,) * 6,
                    nature: Nature = Nature.SERIOUS) -> Stats:
    new_stats = [
        calculate_stat(
            base_stats[PermStat.MAX_HP],
            ivs[0],
            evs[0],
            level
        ) + level + 10,
        calculate_stat(
            base_stats[PermStat.ATTACK],
            ivs[1],
            evs[1],
            level
        ) + 5,
        calculate_stat(
            base_stats[PermStat.DEFENSE],
            ivs[2],
            evs[2],
            level
        ) + 5,
        calculate_stat(
            base_stats[PermStat.SPECIAL_ATTACK],
            ivs[3],
            evs[3],
            level
        ) + 5,
        calculate_stat(
            base_stats[PermStat.SPECIAL_DEFENSE],
            ivs[4],
            evs[4],
            level
        ) + 5,
        calculate_stat(
            base_stats[PermStat.SPEED],
            ivs[5],
            evs[5],
            level
        ) + 5]
    new_stats = update_stats_from_nature(new_stats, nature)
    new_stats = [int(v) for v in new_stats]
    return tuple(new_stats)


class Pokemon:
    __slots__ = ('species', 'moves', 'level', 'evs', 'ivs', 'nature', 'stats')

    def __init__(self,
                 species: PokemonSpecies,
                 moves: List[Move],
                 level: int = 100,
                 evs: Stats = (85,) * 6,
                 ivs: Stats = (31,) * 6,
                 nature: Nature = Nature.SERIOUS):
        self.species = species
        self.moves = moves
        self.level = level
        self.evs = evs
        self.ivs = ivs
        self.nature = nature
        self.stats = calculate_stats(self.species.base_stats, self.level, self.ivs, self.evs, self.nature)

    def __str__(self):
        return "Stats " + str(self.stats) + ", Types " + str([t.name for t in self.species.types])


class BattlingPokemon:
    __slots__ = ('constants', 'hp', 'types', 'boosts', 'status', 'battling_moves')

    def __init__(self, constants: Pokemon):
        self.constants = constants
        self.hp = constants.stats[PermStat.MAX_HP]
        self.types = constants.species.types
        self.boosts = (0,) * 6
        self.status = Status.NONE
        self.battling_moves = [BattlingMove(m) for m in constants.moves]

    def __str__(self):
        return (("Stats " + str(self.constants.stats) + ", Types " + str([t.name for t in self.types]) + ", HP "
                + str(self.hp)) + ", Boosts " + str(self.boosts[1:]) +
                (", " + self.status.name if self.status != Status.NONE else ""))

    def reset(self):
        self.hp = self.constants.stats[PermStat.MAX_HP]
        self.types = self.constants.species.types
        self.boosts = (0,) * 6
        self.status = Status.NONE
        for move in self.battling_moves:
            move.reset()
