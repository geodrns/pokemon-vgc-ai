from numpy import clip
from numpy.random import Generator, default_rng

from vgc2.battle_engine.damage_calculator import calculate_damage, calculate_poison_damage, calculate_sand_damage, \
    calculate_burn_damage, calculate_stealth_rock_damage
from vgc2.battle_engine.game_state import State, Side
from vgc2.battle_engine.modifiers import Weather, Terrain, Hazard, Status, Category, Type
from vgc2.battle_engine.move import Move, BattlingMove
from vgc2.battle_engine.pokemon import BattlingPokemon
from vgc2.battle_engine.priority_calculator import priority_calculator
from vgc2.battle_engine.team import Team, BattlingTeam
from vgc2.battle_engine.threshold_calculator import paralysis_threshold, move_hit_threshold, thaw_threshold
from vgc2.battle_engine.view import StateView, TeamView

BattleCommand = tuple[int, int]  # action, target
FullCommand = tuple[list[BattleCommand], list[BattleCommand]]

_rng = default_rng()
struggle = BattlingMove(Move(Type.TYPELESS, 50, 1., 0, Category.PHYSICAL, recoil=.5))


class BattleEngine:  # TODO Debug mode
    class TeamFainted(Exception):
        pass

    __slots__ = ('n_active', 'state', 'state_view', 'winning_side', 'rng', 'struggle', '_move_queue', '_switch_queue')

    def __init__(self, n_active: int = 2, rng: Generator = _rng):
        self.n_active = n_active
        self.state = State()
        self.state_view = StateView(self.state, 0), StateView(self.state, 1)
        self.winning_side: int = -1
        self.rng = rng
        self._move_queue: list[tuple[int, BattlingPokemon, BattlingMove, list[BattlingPokemon]]] = []
        self._switch_queue: list[tuple[int, int, int]] = []

    def __str__(self):
        return str(self.state)

    def reset(self):
        self.state.reset()
        self.winning_side = -1
        self._move_queue = []
        self._switch_queue = []

    def set_teams(self,
                  teams: tuple[Team, Team],
                  views: tuple[TeamView, TeamView] | None = None):
        if not views:
            views = TeamView(teams[0]), TeamView(teams[1])
        self.state.sides[0].set_team(BattlingTeam(teams[0].members[:self.n_active],
                                                  teams[0].members[self.n_active:]), views[1])
        self.state.sides[1].set_team(BattlingTeam(teams[1].members[:self.n_active],
                                                  teams[1].members[self.n_active:]), views[0])
        for s in self.state.sides:
            s.team._engine = self
            for p in s.team.active + s.team.reserve:
                p._engine = self

    def run_turn(self,
                 commands: FullCommand):
        self._set_action_queue(commands)
        try:
            self._perform_switches()
            self._perform_moves()
            self._end_of_turn_state_effects()
        except BattleEngine.TeamFainted:
            if self.state.sides[1].team.fainted() and not self.state.sides[0].team.fainted():
                self.winning_side = 0
            if self.state.sides[0].team.fainted() and not self.state.sides[1].team.fainted():
                self.winning_side = 1
            return
        self.state._on_turn_end()

    def finished(self) -> bool:
        return self.state.terminal()

    def _set_action_queue(self,
                          commands: FullCommand):
        for side in (0, 1):
            for i, a in enumerate(commands[side]):
                if i >= len(self.state.sides[side].team.active):
                    continue
                if a[0] >= 0:
                    user = self.state.sides[side].team.active[i]
                    def_act = self.state.sides[not side].team.active
                    self._move_queue += [(side, user, user.battling_moves[a[0]],
                                          [def_act[a[1] if a[1] < len(def_act) else 0]])]
                else:
                    self._switch_queue += [(side, i, a[1])]

    def _perform_switches(self):
        while len(self._switch_queue) > 0:
            side, active, reserve = self._switch_queue.pop()
            self.state.sides[side].team.switch(active, reserve)

    def _perform_moves(self):
        while len(self._move_queue) > 0:
            # determine next move
            side, attacker, _move, defenders = (
                self._move_queue.pop(max(enumerate([priority_calculator(a[2].constants, a[1], self.state) for a in
                                                    self._move_queue]), key=lambda x: x[1])[0]))
            # before each move check if Pokémon can attack due status or have its status removed
            if all(m.pp == 0 for m in attacker.battling_moves):
                _move = struggle
            elif self._perform_status(attacker, _move.constants):
                continue
            elif _move.disabled or _move.pp == 0:
                _move = next(m for m in attacker.battling_moves if m.pp > 0 and not m.disabled)
            damage, protected, failed = 0, False, True
            if _move != struggle:
                _move.pp = max(0, _move.pp - 1)
                attacker.on_move_used(_move)
            for defender in defenders:
                if defender.protect:
                    protected = True
                    continue
                if self.rng.random() >= move_hit_threshold(_move.constants, attacker, defender):
                    continue
                failed = False
                # perform next move, damaged is applied first and then effects, unless opponent protected itself
                damage = calculate_damage(side, _move.constants, self.state, attacker, defender)
                defender.deal_damage(damage)
                if defender.fainted():
                    continue
                if self.rng.random() < _move.constants.effect_prob:
                    self._perform_target_effects(_move.constants, side, defender)
                # a fire move will thaw a frozen target
                if _move.constants.pkm_type == Type.FIRE and damage > 0 and defender.status == Status.FROZEN:
                    defender.status = Status.NONE
            if not protected and not failed and self.rng.random() < _move.constants.effect_prob:
                self._perform_single_effects(_move.constants, side, attacker, damage)

    def _perform_status(self,
                        attacker: BattlingPokemon,
                        _move: Move) -> bool:
        match attacker.status:
            case Status.PARALYZED:
                if self.rng.random() < paralysis_threshold():
                    return True
            case Status.SLEEP:
                if attacker._wake_turns == 0:
                    attacker.status = Status.NONE
                else:
                    return True
            case Status.FROZEN:
                if _move.pkm_type == Type.FIRE or self.rng.random() < thaw_threshold():
                    attacker.status = Status.NONE
                else:
                    return True
        return False

    def _perform_single_effects(self,
                                move: Move,
                                side: int,
                                attacker: BattlingPokemon,
                                damage: float):
        # State changes
        if move.weather_start != Weather.CLEAR and move.weather_start != self.state.weather:
            self.state.weather = move.weather_start
        elif move.field_start != Terrain.NONE and move.field_start != self.state.field:
            self.state.field = move.field_start
        elif move.toggle_trickroom and not self.state.trickroom:
            self.state.trickroom = True
        # Side conditions changes
        elif move.toggle_lightscreen and not self.state.sides[side].conditions.lightscreen:
            self.state.sides[side].conditions.lightscreen = True
        elif move.toggle_reflect and not self.state.sides[side].conditions.reflect:
            self.state.sides[side].conditions.reflect = True
        elif move.toggle_tailwind and not self.state.sides[side].conditions.tailwind:
            self.state.sides[side].conditions.tailwind = True
        elif move.hazard == Hazard.STEALTH_ROCK:
            self.state.sides[side].conditions.stealth_rock = True
        elif move.hazard == Hazard.TOXIC_SPIKES:
            self.state.sides[side].conditions.poison_spikes = True
        # Pokémon effects
        elif move.heal > 0:
            attacker.recover(int(damage * move.heal))
        elif move.recoil > 0:
            attacker.deal_damage(int(damage * move.recoil))
        elif move.self_switch:
            self.state.sides[side].team.switch(self.state.sides[side].team.get_active_pos(attacker),
                                               self.state.sides[side].team.first_from_reserve())
        elif move.change_type:
            attacker.types = [attacker.battling_moves[0].constants.pkm_type]
        elif any(b > 0 for b in move.boosts):
            attacker.boosts = [int(clip(_b + b, -6, 6)) for _b, b in zip(attacker.boosts, move.boosts)]
        elif move.protect:
            attacker.protect = True

    def _perform_target_effects(self,
                                move: Move,
                                side: int,
                                defender: BattlingPokemon):
        # Pokémon effects
        if move.status != Status.NONE and defender.status == Status.NONE:
            defender.status = move.status
        # Move Effects
        elif move.disable and not any(
                m.disabled for m in defender.battling_moves) and defender.last_used_move is not None:
            defender.last_used_move.disabled = True
        elif move.force_switch:
            self.state.sides[not side].team.switch(self.state.sides[not side].team.get_active_pos(defender),
                                                   self.state.sides[not side].team.first_from_reserve())

    def _end_of_turn_state_effects(self):
        all_active = self.state.sides[0].team.active + self.state.sides[1].team.active
        for pkm in all_active:
            if pkm.status == Status.POISON:
                pkm.deal_damage(calculate_poison_damage(pkm))
        for pkm in all_active:
            if pkm.status == Status.BURN:
                pkm.deal_damage(calculate_burn_damage(pkm))
        for pkm in all_active:
            if self.state.weather == Weather.SAND:
                pkm.deal_damage(calculate_sand_damage(pkm))

    def _on_fainted(self,
                    pkm: BattlingPokemon):
        side = self.state.get_side(pkm)
        if self.state.sides[side].team.fainted():
            raise BattleEngine.TeamFainted()
        self.state.sides[side].team.switch(self.state.sides[side].team.get_active_pos(pkm),
                                           self.state.sides[side].team.first_from_reserve())

    def _on_switch(self,
                   switch_in: BattlingPokemon | None,
                   switch_out: BattlingPokemon):
        # if a Pokémon switches out it will no longer perform its moves
        self._move_queue = [a for a in self._move_queue if a[1] != switch_out]
        # hazards
        if not switch_in:
            return
        side = self.state.get_side(switch_in)
        if (self.state.sides[side].conditions.poison_spikes and Type.POISON not in switch_in.types and
                Type.STEEL not in switch_in.types and switch_in.status == Status.NONE):
            switch_in.status = Status.POISON
        if self.state.sides[side].conditions.stealth_rock:
            switch_in.deal_damage(calculate_stealth_rock_damage(switch_in))
