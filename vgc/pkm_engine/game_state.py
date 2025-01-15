from vgc.pkm_engine.modifiers import Weather, Terrain
from vgc.pkm_engine.pokemon import BattlingPokemon


class SideConditions:
    __slots__ = ('reflect', '_reflect_turns', 'lightscreen', '_lightscreen_turns', 'tailwind', '_tailwind_turns',
                 'stealth_rock', 'poison_spikes')

    def __init__(self):
        self.reflect = False
        self._reflect_turns = 0
        self.lightscreen = False
        self._lightscreen_turns = 0
        self.tailwind = False
        self._tailwind_turns = 0
        self.stealth_rock = False
        self.poison_spikes = False

    def __str__(self):
        return ((", Reflect" if self.reflect else "") +
                (", Light Screen" if self.lightscreen else "") +
                (", Tailwind" if self.tailwind else "") +
                (", Stealth Rock" if self.stealth_rock else "") +
                (", Poison Spikes" if self.poison_spikes else ""))

    def reset(self):
        self.reflect = False
        self._reflect_turns = 0
        self.lightscreen = False
        self._lightscreen_turns = 0
        self.tailwind = False
        self._tailwind_turns = 0
        self.stealth_rock = False
        self.poison_spikes = False

    def on_turn_end(self):
        if self.reflect:
            self._reflect_turns += 1
            if self._reflect_turns >= 5:
                self.reflect = False
                self._reflect_turns = 0
        if self.lightscreen:
            self._lightscreen_turns += 1
            if self._lightscreen_turns >= 5:
                self.lightscreen = False
                self._lightscreen_turns = 0
        if self.tailwind:
            self._tailwind_turns += 1
            if self._tailwind_turns >= 5:
                self.tailwind = False
                self._tailwind_turns = 0


class Side:
    __slots__ = ('active', '_initial_active', 'reserve', '_initial_reserve', 'wish', 'conditions', 'future_sight',
                 '_engine')

    def __init__(self,
                 active: list[BattlingPokemon],
                 reserve: list[BattlingPokemon]):
        self.active = active
        self._initial_active = active[:]
        self.reserve = reserve
        self._initial_reserve = active[:]
        self.conditions = SideConditions()
        self._engine = None

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
               reserve_pos: int):
        if active_pos < 0 or reserve_pos < 0:
            return
        old_reserve = self.reserve[reserve_pos]
        if old_reserve.fainted():
            return False
        old_active = self.active[active_pos]
        old_active.on_switch()
        self.reserve[reserve_pos] = old_active
        self.active[active_pos] = old_reserve
        self._engine._on_switch(old_reserve, old_active)

    def on_turn_end(self):
        self.conditions.on_turn_end()
        for active in self.active:
            active.on_turn_end()

    def team_fainted(self) -> bool:
        return all(p.fainted() for p in self.active + self.reserve)

    def get_active_pos(self,
                       pkm: BattlingPokemon) -> int:
        return next((i for i, p in enumerate(self.active) if p == pkm), -1)

    def first_from_reserve(self) -> int:
        return next((i for i, p in enumerate(self.reserve) if not p.fainted()), -1)


class State:
    __slots__ = ('sides', 'weather', '_weather_turns', 'field', '_field_turns', 'trickroom', '_trickroom_turns')

    def __init__(self,
                 sides: tuple[Side, Side]):
        self.sides = sides
        self.weather = Weather.CLEAR
        self._weather_turns = 0
        self.field = Terrain.NONE
        self._field_turns = 0
        self.trickroom = False
        self._trickroom_turns = 0

    def __str__(self):
        return ((", Weather " + self.weather.name if self.weather != Weather.CLEAR else "") +
                (", Terrain " + self.field.name if self.field != Terrain.NONE else "") +
                (", Trickroom" if self.trickroom else "") +
                "Side 0 " + str(self.sides[0]) + ", Side 1 " + str(self.sides[1]))

    def reset(self):
        for side in self.sides:
            side.reset()
        self.weather = Weather.CLEAR
        self._weather_turns = 0
        self.field = Terrain.NONE
        self._field_turns = 0
        self.trickroom = False
        self._trickroom_turns = 0

    def on_turn_end(self):
        # weather advance
        if self.weather != Weather.CLEAR:
            self._weather_turns += 1
            if self._weather_turns >= 5:
                self._weather_turns = 0
                self.weather = Weather.CLEAR
        # terrain advance
        if self.field != Terrain.NONE:
            self._field_turns += 1
            if self._field_turns >= 5:
                self._field_turns = 0
                self.field = Terrain.NONE
        # trickroom advance
        if self.trickroom:
            self._trickroom_turns += 1
            if self._trickroom_turns >= 5:
                self.trickroom = False
                self._trickroom_turns = 0
        for side in self.sides:
            side.on_turn_end()

    def terminal(self):
        return any(s.team_fainted() for s in self.sides)

    def get_side(self,
                 pkm: BattlingPokemon) -> int:
        if pkm in self.sides[0].active:
            return 0
        if pkm in self.sides[0].reserve:
            return 0
        if pkm in self.sides[1].active:
            return 1
        if pkm in self.sides[0].reserve:
            return 1
        return -1
