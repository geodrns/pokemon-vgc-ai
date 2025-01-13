from typing import List, Tuple

from vgc.pkm_engine.modifiers import Weather, Terrain
from vgc.pkm_engine.pokemon import BattlingPokemon


class SideConditions:
    __slots__ = ('reflect', 'lightscreen', 'tailwind')

    def __init__(self):
        self.reflect = False
        self.lightscreen = False
        self.tailwind = False

    def reset(self):
        self.reflect = False
        self.lightscreen = False
        self.tailwind = False


class Side:
    __slots__ = ('active', 'reserve', 'wish', 'conditions', 'future_sight')

    def __init__(self, active: List[BattlingPokemon], reserve: List[BattlingPokemon]):
        self.active = active
        self.reserve = reserve
        self.conditions = SideConditions()

    def reset(self):
        for pkm in self.active:
            pkm.reset()
        for pkm in self.reserve:
            pkm.reset()
        self.conditions.reset()


class State:
    __slots__ = ('sides', 'weather', 'field', 'trick_room')

    def __init__(self, sides: Tuple[Side, Side]):
        self.sides = sides
        self.weather = Weather.CLEAR
        self.field = Terrain.NONE
        self.trick_room = False

    def reset(self):
        for side in self.sides:
            side.reset()
        self.weather = Weather.CLEAR
        self.field = Terrain.NONE
        self.trick_room = False
