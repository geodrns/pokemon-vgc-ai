from vgc2.pkm_engine.pokemon import BattlingPokemon, Pokemon


class Team:
    __slots__ = ('members',)

    def __init__(self,
                 members: list[Pokemon]):
        self.members = members

    def __str__(self):
        return str([str(m) for m in self.members])

    def subteam(self,
                idx: list[int]):  # -> Self
        members: list[Pokemon] = []
        for i in idx:
            members += [self.members[i]]
        return Team(members)


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
