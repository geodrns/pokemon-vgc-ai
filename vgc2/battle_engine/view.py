from vgc2.battle_engine.game_state import Side, State
from vgc2.battle_engine.pokemon import Pokemon, BattlingPokemon
from vgc2.battle_engine.team import Team, BattlingTeam


class InvalidAttrAccessException(Exception):
    pass


class PokemonView(Pokemon):
    __slots__ = ('_pkm', '_revealed')

    def __init__(self,
                 pkm: Pokemon):
        self._pkm = pkm
        self._pkm._views += [self]
        self._revealed: list[int] = []

    def __del__(self):
        self._pkm._views.remove(self)

    def __str__(self):
        return "Types " + str([t.name for t in self.species.types]) + ", Moves " + str([str(m) for m in self.moves])

    def __getattr__(self,
                    attr):
        if attr == "moves":
            return [self._pkm.moves[i] for i in self._revealed]
        if attr in ["evs", "ivs", "nature", "stats", "_pkm"]:
            raise InvalidAttrAccessException()
        return getattr(self._pkm, attr)

    def _on_move_used(self,
                      i: int):
        if i not in self._revealed:
            self._revealed += [i]

    def hide(self):
        self._revealed = []


class BattlingPokemonView(BattlingPokemon):
    __slots__ = ('_pkm', '_constants_view', '_revealed')

    def __init__(self,
                 pkm: BattlingPokemon):
        self._pkm = pkm
        self._constants_view = PokemonView(self._pkm.constants)
        self._pkm.constants._views += [self]
        self._revealed: list[int] = []

    def __del__(self):
        self._pkm.constants._views.remove(self)

    def __getattr__(self,
                    attr):
        if attr == "_pkm":
            raise InvalidAttrAccessException()
        if attr == "constants":
            return self._constants_view
        if attr == "battling_moves":
            return [self._pkm.battling_moves[i] for i in self._revealed]
        return getattr(self._pkm, attr)

    def _on_move_used(self,
                      i: int):
        if i not in self._revealed:
            self._revealed += [i]

    def hide(self):
        self._revealed = []


class TeamView(Team):
    __slots__ = ('_team', '_members')

    def __init__(self, team: Team):
        self._team = team
        self._members = [PokemonView(p) for p in team.members]

    def __getattr__(self,
                    attr):
        if attr == "_team":
            raise InvalidAttrAccessException()
        if attr == "members":
            return self._members
        return getattr(self._team, attr)

    def hide(self):
        for m in self._members:
            m.hide()


class BattlingTeamView(BattlingTeam):
    __slots__ = ('_team', '_active', '_reserve')

    def __init__(self, team: BattlingTeam):
        self._team = team
        self._active = [BattlingPokemonView(p) for p in self._team.active]
        self._reserve = [BattlingPokemonView(p) for p in self._team.reserve]
        self._team._views += [self]

    def __del__(self):
        self._team._views.remove(self)

    def __getattr__(self,
                    attr):
        if attr == "_team":
            raise InvalidAttrAccessException()
        if attr == "active":
            return self._active
        if attr == "reserve":
            return self._reserve
        return getattr(self._pkm, attr)

    def on_switch(self,
                  active_pos: int,
                  reserve_pos: int):
        old_reserve = self._reserve[reserve_pos]
        old_active = self._active[active_pos]
        self._reserve[reserve_pos] = old_active
        self._active[active_pos] = old_reserve


class SideView(Side):
    __slots__ = ('_side', '_team')

    def __init__(self, side: Side):
        self._side = side
        self._team = BattlingTeamView(self._side.team)

    def __getattr__(self,
                    attr):
        if attr == "_side":
            raise InvalidAttrAccessException()
        if attr == "team":
            return self._team
        return getattr(self._pkm, attr)


class StateView(State):
    __slots__ = ('_state', '_sides')

    def __init__(self, state: State, side: int):
        self._state = state
        self._sides = (state.sides[side], SideView(state.sides[not side]))

    def __getattr__(self,
                    attr):
        if attr == "_state":
            raise InvalidAttrAccessException()
        if attr == "sides":
            return self._sides
        return getattr(self._pkm, attr)
