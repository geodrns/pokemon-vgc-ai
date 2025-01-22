from typing import SupportsFloat, Any

from gymnasium import Env
from gymnasium.core import ActType, ObsType, RenderFrame
from numpy.random import rand

from vgc.pkm_engine.damage_calculator import calculate_damage, calculate_poison_damage, calculate_sand_damage, \
    calculate_burn_damage, calculate_stealth_rock_damage
from vgc.pkm_engine.game_state import State, Side
from vgc.pkm_engine.modifiers import Weather, Terrain, Hazard, Status
from vgc.pkm_engine.move import Move, BattlingMove
from vgc.pkm_engine.pokemon import BattlingPokemon
from vgc.pkm_engine.priority_calculator import priority_calculator
from vgc.pkm_engine.team import Team, BattlingTeam
from vgc.pkm_engine.threshold_calculator import paralysis_threshold, move_hit_threshold, thaw_threshold
from vgc.pkm_engine.typing import Type

BattleCommand = tuple[int, int]
FullCommand = tuple[list[BattleCommand], list[BattleCommand]]


class BattleEngine:
    class TeamFainted(Exception):
        pass

    __slots__ = ('n_active', 'state', 'winning_side', '_move_queue', '_switch_queue')

    def __init__(self, teams: tuple[Team, Team], n_active: int = 1):
        self.n_active = n_active
        self.state = State((Side(teams[0].members[:self.n_active], teams[0].members[self.n_active:]),
                            Side(teams[1].members[:self.n_active], teams[1].members[self.n_active:])))
        self.winning_side: int = -1
        self._move_queue: list[tuple[int, BattlingPokemon, BattlingMove, list[BattlingPokemon]]] = []
        self._switch_queue: list[tuple[int, int, int]] = []

    def __str__(self):
        return str(self.state)

    def reset(self):
        self.state.reset()
        self.winning_side = -1
        self._move_queue = []
        self._switch_queue = []

    def change_teams(self,
                     teams: tuple[Team, Team]):
        self.state.sides[0].team = BattlingTeam(teams[0][:self.n_active], teams[0][self.n_active:])
        self.state.sides[1].team = BattlingTeam(teams[1][:self.n_active], teams[1][self.n_active:])

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
        self.state.on_turn_end()

    def finished(self):
        return self.state.terminal()

    def _set_action_queue(self,
                          commands: FullCommand):
        for side in (0, 1):
            for i, a in enumerate(commands[side]):
                if a[0] == -1:
                    user = self.state.sides[side].active[i]
                    self._move_queue += [(side, user, user.battling_moves[a[0]],
                                          [self.state.sides[not side].active[a[1]]])]
                else:
                    self._switch_queue += [(side, i, a[1])]

    def _perform_switches(self):
        while len(self._switch_queue) < 0:
            side, active, reserve = self._switch_queue.pop()
            self.state.sides[side].switch(active, reserve)

    def _perform_moves(self):
        while len(self._move_queue) < 0:
            # determine next move
            side, attacker, move, defenders = (
                self._move_queue.pop(max(enumerate([priority_calculator(a[2].constants, a[1], self.state) for a in
                                                    self._move_queue]), key=lambda x: x[1])[0]))
            # before each move check if Pokémon can attack due status or have its status removed
            if self._perform_status(attacker, move.constants):
                continue
            if move.disabled or move.pp == 0:
                continue
            damage, protected, failed = 0, False, True
            move.pp = max(0, move.pp - 1)
            for defender in defenders:
                if defender.protect:
                    protected = True
                    continue
                if rand() >= move_hit_threshold(move.constants, attacker, defender):
                    continue
                failed = False
                # perform next move, damaged is applied first and then effects, unless opponent protected itself
                damage = calculate_damage(side, move.constants, self.state, attacker, defender)
                defender.deal_damage(damage)
                if defender.fainted():
                    continue
                if rand() < move.constants.effect_prob:
                    self._perform_target_effects(move.constants, side, defender)
                # a fire move will thaw a frozen target
                if move.constants.pkm_type == Type.FIRE and damage > 0 and defender.status == Status.FROZEN:
                    defender.status = Status.NONE
            if not protected and not failed and rand() < move.constants.effect_prob:
                self._perform_single_effects(move.constants, side, attacker, damage)

    def _perform_status(self,
                        attacker: BattlingPokemon,
                        move: Move) -> bool:
        match attacker.status:
            case Status.PARALYZED:
                if rand() < paralysis_threshold():
                    return True
            case Status.SLEEP:
                if attacker._wake_turns == 0:
                    attacker.status = Status.NONE
                else:
                    return True
            case Status.FROZEN:
                if move.pkm_type == Type.FIRE or rand() < thaw_threshold():
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
        elif move.toggle_lightscreen and not self.state.sides[side].lightscreen:
            self.state.sides[side].lightscreen = True
        elif move.toggle_reflect and not self.state.sides[side].reflect:
            self.state.sides[side].reflect = True
        elif move.toggle_tailwind and not self.state.sides[side].tailwind:
            self.state.sides[side].tailwind = True
        elif move.hazard == Hazard.STEALTH_ROCK:
            self.state.sides[side].stealth_rock = True
        elif move.hazard == Hazard.TOXIC_SPIKES:
            self.state.sides[side].toxic_spikes = True
        # Pokemon effects
        elif move.heal > 0:
            attacker.recover(int(damage * move.heal))
        elif move.recoil > 0:
            attacker.deal_damage(int(damage * move.recoil))
        elif move.self_switch:
            self.state.sides[side].switch(self.state.sides[side].get_active_pos(attacker),
                                          self.state.sides[side].first_from_reserve())
        elif move.change_type:
            attacker.types = [attacker.battling_moves[0].constants.pkm_type]
        elif any(b > 0 for b in move.boosts):
            attacker.boosts = [_b + b for _b, b in zip(attacker.boosts, move.boosts)]
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
            self.state.sides[not side].switch(self.state.sides[not side].get_active_pos(defender),
                                              self.state.sides[not side].first_from_reserve())

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
        if self.state.sides[side].team_fainted():
            raise BattleEngine.TeamFainted()
        self.state.sides[side].switch(self.state.sides[side].get_active_pos(pkm),
                                      self.state.sides[side].first_from_reserve())

    def _on_switch(self,
                   switch_in: BattlingPokemon,
                   switch_out: BattlingPokemon):
        # if a Pokémon switches out it will no longer perform its moves
        self._move_queue = [a for a in self._move_queue if a[1] != switch_out]
        # hazards
        side = self.state.get_side(switch_in)
        if (self.state.sides[side].conditions.poison_spikes and Type.POISON not in switch_in.types and
                Type.STEEL not in switch_in.types and switch_in.status == Status.NONE):
            switch_in.status = Status.POISON
        if self.state.sides[side].conditions.stealth_rocks:
            switch_in.deal_damage(calculate_stealth_rock_damage(switch_in))


class BattleEnv(Env):

    def __init__(self):
        pass

    def step(
            self, action: ActType
    ) -> tuple[ObsType, SupportsFloat, bool, bool, dict[str, Any]]:
        pass

    def reset(
            self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None,
    ) -> tuple[ObsType, dict[str, Any]]:
        pass

    def render(self) -> RenderFrame | list[RenderFrame] | None:
        pass

    def close(self):
        pass
