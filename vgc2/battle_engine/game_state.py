from vgc2.battle_engine.constants import WEATHER_TURNS, TERRAIN_TURNS, TRICKROOM_TURNS, REFLECT_TURNS, \
    LIGHTSCREEN_TURNS, \
    TAILWIND_TURNS
from vgc2.battle_engine.modifiers import Weather, Terrain
from vgc2.battle_engine.pokemon import BattlingPokemon, Pokemon
from vgc2.battle_engine.team import BattlingTeam


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
            if self._reflect_turns >= REFLECT_TURNS:
                self.reflect = False
                self._reflect_turns = 0
        if self.lightscreen:
            self._lightscreen_turns += 1
            if self._lightscreen_turns >= LIGHTSCREEN_TURNS:
                self.lightscreen = False
                self._lightscreen_turns = 0
        if self.tailwind:
            self._tailwind_turns += 1
            if self._tailwind_turns >= TAILWIND_TURNS:
                self.tailwind = False
                self._tailwind_turns = 0


class Side:
    __slots__ = ('team', 'conditions', '_engine')

    def __init__(self,
                 active: list[Pokemon],
                 reserve: list[Pokemon]):
        self.team = BattlingTeam(active, reserve)
        self.conditions = SideConditions()
        self._engine = None

    def __str__(self):
        return str(self.team) + str(self.conditions)

    def reset(self):
        self.team.reset()
        self.conditions.reset()

    def on_turn_end(self):
        self.conditions.on_turn_end()
        self.team.on_turn_end()


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
            if self._weather_turns >= WEATHER_TURNS:
                self._weather_turns = 0
                self.weather = Weather.CLEAR
        # terrain advance
        if self.field != Terrain.NONE:
            self._field_turns += 1
            if self._field_turns >= TERRAIN_TURNS:
                self._field_turns = 0
                self.field = Terrain.NONE
        # trickroom advance
        if self.trickroom:
            self._trickroom_turns += 1
            if self._trickroom_turns >= TRICKROOM_TURNS:
                self.trickroom = False
                self._trickroom_turns = 0
        for side in self.sides:
            side.on_turn_end()

    def terminal(self):
        return any(s.team.fainted() for s in self.sides)

    def get_side(self,
                 pkm: BattlingPokemon) -> int:
        return 0 if pkm in self.sides[0].team.active or pkm in self.sides[0].team.reserve else 1
