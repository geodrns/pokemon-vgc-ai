from vgc.pkm_engine.pokemon import BattlingPokemon, Pokemon, PokemonView, InvalidAttrAccessException, \
    BattlingPokemonView


class Team:
    __slots__ = ('members',)

    def __init__(self,
                 members: list[Pokemon]):
        self.members = members

    def __str__(self):
        return str([str(m) for m in self.members])


class BattlingTeam:
    __slots__ = ('active', '_initial_active', 'reserve', '_initial_reserve', '_views')

    def __init__(self, active: list[Pokemon], reserve: list[Pokemon]):
        self.active = [BattlingPokemon(p) for p in active]
        self._initial_active = self.active[:]
        self.reserve = [BattlingPokemon(p) for p in reserve]
        self._initial_reserve = self.active[:]
        self._views = []

    def __str__(self):
        return "Active " + str([str(a) for a in self.active]) + ", Reserve " + str([str(r) for r in self.reserve])

    def reset(self):
        self.active = self._initial_active[:]
        self.reserve = self._initial_reserve[:]
        for pkm in self.active:
            pkm.reset()
        for pkm in self.reserve:
            pkm.reset()

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
        for v in self._views:
            v.on_switch(active_pos, reserve_pos)
        self.reserve[reserve_pos] = old_active
        self.active[active_pos] = old_reserve

    def on_turn_end(self):
        for active in self.active:
            active.on_turn_end()

    def fainted(self) -> bool:
        return all(p.fainted() for p in self.active + self.reserve)

    def get_active_pos(self,
                       pkm: BattlingPokemon) -> int:
        return next((i for i, p in enumerate(self.active) if p == pkm), -1)

    def first_from_reserve(self) -> int:
        return next((i for i, p in enumerate(self.reserve) if not p.fainted()), -1)


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
