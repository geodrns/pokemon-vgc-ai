import math
from typing import List, Optional

from vgc.pkm_engine.constants import NATURES
from vgc.pkm_engine.modifiers import Stat, Status, Stats
from vgc.pkm_engine.move import Move, BattlingMove
from vgc.pkm_engine.nature import Nature
from vgc.pkm_engine.typing import Type


class PokemonSpecies:
    __slots__ = ('id', 'base_stats', 'types', 'moves', '_instances')

    def __init__(self,
                 base_stats: Stats,
                 types: List[Type],
                 moves: List[Move]):
        self.id = -1
        self.base_stats = base_stats
        self.types = types
        self.moves = moves
        self._instances = []

    def __str__(self):
        return ("Base Stats " + str(self.base_stats) +
                ", Types " + str([t.name for t in self.types]) +
                ", Moves " + str([str(m) for m in self.moves]))

    def edit(self,
             base_stats: Stats,
             types: List[Type],
             moves: List[Move]):
        self.base_stats = base_stats
        self.types = types
        self.moves = moves
        for pkm in self._instances:
            pkm._edit_stats()


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
            base_stats[Stat.MAX_HP],
            ivs[0],
            evs[0],
            level
        ) + level + 10,
        calculate_stat(
            base_stats[Stat.ATTACK],
            ivs[1],
            evs[1],
            level
        ) + 5,
        calculate_stat(
            base_stats[Stat.DEFENSE],
            ivs[2],
            evs[2],
            level
        ) + 5,
        calculate_stat(
            base_stats[Stat.SPECIAL_ATTACK],
            ivs[3],
            evs[3],
            level
        ) + 5,
        calculate_stat(
            base_stats[Stat.SPECIAL_DEFENSE],
            ivs[4],
            evs[4],
            level
        ) + 5,
        calculate_stat(
            base_stats[Stat.SPEED],
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
                 move_indexes: List[int],
                 level: int = 100,
                 evs: Stats = (85,) * 6,
                 ivs: Stats = (31,) * 6,
                 nature: Nature = Nature.SERIOUS):
        self.species = species
        self.moves = [self.species.moves[i] for i in move_indexes if 0 <= i < len(move_indexes)]
        self.level = level
        self.evs = evs
        self.ivs = ivs
        self.nature = nature
        self.stats = calculate_stats(self.species.base_stats, self.level, self.ivs, self.evs, self.nature)
        self.species._instances += [self]

    def __str__(self):
        return ("Stats " + str(self.stats) +
                ", Types " + str([t.name for t in self.species.types]) +
                ", Moves " + str([str(m) for m in self.moves]))

    def __del__(self):
        self.species._instances.remove(self)

    def _edit_stats(self):
        self.stats = calculate_stats(self.species.base_stats, self.level, self.ivs, self.evs, self.nature)

    def edit(self,
             move_indexes: List[int],
             level: int = 100,
             evs: Stats = (85,) * 6,
             ivs: Stats = (31,) * 6,
             nature: Nature = Nature.SERIOUS):
        self.moves = [self.species.moves[i] for i in move_indexes if 0 <= i < len(move_indexes)]
        self.level = level
        self.evs = evs
        self.ivs = ivs
        self.nature = nature
        self.stats = calculate_stats(self.species.base_stats, self.level, self.ivs, self.evs, self.nature)


class BattlingPokemon:
    __slots__ = ('constants', 'hp', 'types', 'boosts', 'status', 'battling_moves', 'last_used_move', 'protect')

    def __init__(self,
                 constants: Pokemon):
        self.constants = constants
        self.hp = constants.stats[Stat.MAX_HP]
        self.types = constants.species.types
        self.boosts = [0] * 8  # position 0 is not used
        self.status = Status.NONE
        self.battling_moves = [BattlingMove(m) for m in constants.moves]
        self.last_used_move: Optional[BattlingMove] = None
        self.protect = False

    def __str__(self):
        return ("Stats " + str(self.constants.stats) +
                ", Types " + str([t.name for t in self.types]) +
                ", HP " + str(self.hp) +
                (", Boosts " + str(self.boosts[1:]) if any(b > 0 for b in self.boosts) else "") +
                (", " + self.status.name if self.status != Status.NONE else ""))

    def reset(self):
        self.hp = self.constants.stats[Stat.MAX_HP]
        self.types = self.constants.species.types
        self.boosts = [0] * 8
        self.status = Status.NONE
        for move in self.battling_moves:
            move.reset()
        self.last_used_move = None
        self.protect = False

    def fainted(self):
        return self.hp == 0

    def deal_damage(self, damage: int):
        self.hp = max(0, self.hp - damage)

    def recover(self, heal: int):
        self.hp = min(self.hp + heal, self.constants.species.base_stats[Stat.MAX_HP])

    def switch_reset(self):
        self.boosts = [0] * 8
        for move in self.battling_moves:
            move.disabled = False
        self.last_used_move = None

    def end_of_turn_reset(self):
        self.protect = False
