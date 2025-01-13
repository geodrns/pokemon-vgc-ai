from typing import List, Tuple

from vgc.pkm_engine.modifiers import Weather, Terrain, Hazard
from vgc.pkm_engine.pokemon import BattlingPokemon


class SideConditions:
    __slots__ = ('reflect', 'lightscreen', 'tailwind', 'hazard')

    def __init__(self):
        self.reflect = False
        self.lightscreen = False
        self.tailwind = False
        self.hazard = Hazard.NONE

    def __str__(self):
        return ((", Reflect" if self.reflect else "") +
                (", Light Screen" if self.lightscreen else "") +
                (", Tailwind" if self.tailwind else "") +
                (", Hazard " + self.hazard.name if self.hazard != Hazard.NONE else ""))

    def reset(self):
        self.reflect = False
        self.lightscreen = False
        self.tailwind = False
        self.hazard = Hazard.NONE


class Side:
    __slots__ = ('active', '_initial_active', 'reserve', '_initial_reserve', 'wish', 'conditions', 'future_sight')

    def __init__(self,
                 active: List[BattlingPokemon],
                 reserve: List[BattlingPokemon]):
        self.active = active
        self._initial_active = active[:]
        self.reserve = reserve
        self._initial_reserve = active[:]
        self.conditions = SideConditions()

    def __str__(self):
        return ("Active " + str([str(a) for a in self.active]) + ", Reserve " + str([str(r) for r in self.reserve]) +
                str(self.conditions))

    def reset(self):
        self.active = self._initial_active[:]
        self.reserve = self._initial_reserve[:]
        for pkm in self.active:
            pkm.reset()
        for pkm in self.reserve:
            pkm.reset()
        self.conditions.reset()

    def switch(self,
               active_pos: int,
               reserve_pos: int) -> bool:
        old_reserve = self.reserve[reserve_pos]
        if old_reserve.fainted():
            return False
        old_active = self.active[active_pos]
        self.reserve[reserve_pos] = old_active
        self.active[active_pos] = old_reserve
        return True


class State:
    __slots__ = ('sides', 'weather', 'field', 'trickroom')

    def __init__(self,
                 sides: Tuple[Side, Side]):
        self.sides = sides
        self.weather = Weather.CLEAR
        self.field = Terrain.NONE
        self.trickroom = False

    def __str__(self):
        return ((", Weather " + self.weather.name if self.weather != Weather.CLEAR else "") +
                (", Terrain " + self.field.name if self.field != Terrain.NONE else "") +
                (", Trickroom" if self.trickroom else "") +
                "Side 0 " + str(self.sides[0]) + ", Side 1 " + str(self.sides[1]))

    def reset(self):
        for side in self.sides:
            side.reset()
        self.weather = Weather.CLEAR
        self.field = Terrain.NONE
        self.trickroom = False
