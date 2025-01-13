from enum import IntEnum
from typing import Tuple, List

Stats = Tuple[int, int, int, int, int, int]
MutableStats = List[int]


class Stat:
    # perm
    MAX_HP = 0
    ATTACK = 1
    DEFENSE = 2
    SPECIAL_ATTACK = 3
    SPECIAL_DEFENSE = 4
    SPEED = 5
    # temp
    EVASION = 6
    ACCURACY = 7


class Category(IntEnum):
    OTHER = 0
    PHYSICAL = 1
    SPECIAL = 2


class Status(IntEnum):
    NONE = 0
    SLEEP = 1
    BURN = 2
    FROZEN = 3
    PARALYZED = 4
    POISON = 5
    TOXIC = 6


class Weather(IntEnum):
    CLEAR = 0
    RAIN = 1
    SUN = 2
    SAND = 3
    SNOW = 4


class Hazard(IntEnum):
    NONE = 0
    STEALTH_ROCK = 1
    TOXIC_SPIKES = 2


class Terrain(IntEnum):
    NONE = 0
    ELECTRIC_TERRAIN = 1
    GRASSY_TERRAIN = 2
    MISTY_TERRAIN = 3
    PSYCHIC_TERRAIN = 4
