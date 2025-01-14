from typing import List, Tuple, Type

from numpy.random import rand

from vgc.pkm_engine.damage_calculator import calculate_damage, calculate_poison_damage, calculate_sand_damage, \
    calculate_burn_damage
from vgc.pkm_engine.game_state import State, Side
from vgc.pkm_engine.modifiers import Weather, Terrain, Hazard, Status
from vgc.pkm_engine.move import Move, BattlingMove
from vgc.pkm_engine.pokemon import Pokemon, BattlingPokemon
from vgc.pkm_engine.threshold_calculator import paralysis_threshold, move_hit_threshold

Team = List[Pokemon]
BattlingTeam = List[BattlingPokemon]


def battling_team(team: Team):
    return [BattlingPokemon(p) for p in team]


Action = Tuple[int, int]  # move, target


class BattleEngine:
    class TeamFainted(Exception):
        pass

    __slots__ = ('n_active', 'state', 'winning_side')

    def __init__(self, teams: Tuple[Team, Team], n_active: int = 1):
        battling_teams = (battling_team(teams[0]), battling_team(teams[1]))
        self.n_active = n_active
        self.state = State((
            Side(
                battling_teams[0][:self.n_active],
                battling_teams[0][self.n_active:]
            ),
            Side(
                battling_teams[1][:self.n_active],
                battling_teams[1][self.n_active:]
            )
        ))
        self.winning_side = -1

    def __str__(self):
        return str(self.state)

    def reset(self):
        self.state.reset()
        self.winning_side = -1

    def change_teams(self,
                     teams: Tuple[Team, Team]):
        battling_teams = (battling_team(teams[0]), battling_team(teams[1]))
        self.state.sides[0].active = battling_teams[0][:self.n_active]
        self.state.sides[0].reserve = battling_teams[0][self.n_active:]
        self.state.sides[1].active = battling_teams[1][:self.n_active]
        self.state.sides[1].reserve = battling_teams[1][self.n_active:]

    def run_turn(self,
                 actions: Tuple[List[Action], List[Action]]):
        try:
            self._turn_process(actions)
        except BattleEngine.TeamFainted:
            if self.state.sides[1].team_fainted() and not self.state.sides[0].team_fainted():
                self.winning_side = 0
            if self.state.sides[0].team_fainted() and not self.state.sides[1].team_fainted():
                self.winning_side = 1

    def finished(self):
        return self.state.terminal()

    def _turn_process(self,
                 actions: Tuple[List[Action], List[Action]]):

        all_active_pokemon: List[BattlingPokemon]
        # when team fainted => game ends
        # perform switches
        #   when switch => hazards must be performed,
        #   when fainted => must be switched out
        # if a pokemon switches out it will not longer perform its move
        # determine move order (can be changed after the move effect is applied) (trickroom only affects speed, not priority) (paralyzises cuts speed in 0.5)
        attacker: BattlingPokemon
        defenders: List[BattlingPokemon]
        move: BattlingMove
        side: int
        # before each move check if pokemon can awake or attack due to paralyzises or sleep
        if attacker.status == Status.PARALYZED and rand() < paralysis_threshold():
            pass
        if attacker.status == Status.SLEEP and attacker._wake_turns == 0:
            attacker.status = Status.NONE
        if attacker.status == Status.SLEEP:
            pass
        damage = 0
        rng_attack = rand()
        protected = False
        failed = True
        for defender in defenders:
            if defender.protect:
                protected = True
                continue
            if rng_attack >= move_hit_threshold(move, attacker, defender):
                continue
            failed = False
            # perform one move at the turn, damaged is applied first and then effects, unless opponent protected himself (which probability must be checked)
            damage = calculate_damage(side, move.constants, self.state, attacker, defender)
            defender.deal_damage(damage)
            self.on_damage()
            self._perform_target_effects(move, defender)
            # a fire move will thawn a frozen target
            if move.pkm_type == Type.FIRE and damage > 0 and defender.status == Status.FROZEN:
                defender.status = Status.NONE
        if not protected and not failed:
            self._perform_single_effects(move.constants, side, attacker, damage)
        # apply end of turn effects (one effect at the time, if a pokemon faints, its switched out)
        for pkm in all_active_pokemon:
            if pkm.status == Status.POISON:
                pkm.deal_damage(calculate_poison_damage(pkm))
        self.on_damage()
        for pkm in all_active_pokemon:
            if pkm.status == Status.BURN:
                pkm.deal_damage(calculate_burn_damage(pkm))
        self.on_damage()
        for pkm in all_active_pokemon:
            if self.state.weather == Weather.SAND:
                pkm.deal_damage(calculate_sand_damage(pkm))

        # advance end turn state
        self.state.on_turn_end()

    def _perform_switches(self,
                          actions: Tuple[List[Action], List[Action]]):
        switches = []
        for i, s in enumerate(actions):
            for j, a in enumerate(s):
                if a[0] == -1:
                    switches += [(i, j, a[1])]
        while len(switches) < 0:
            s, act, rsv = switches.pop()
            self.state.sides[s].switch(act, rsv)

    def _perform_single_effects(self,
                                move: Move,
                                side: int,
                                attacker: BattlingPokemon,
                                damage: float):
        # state changes
        if move.weather_start != Weather.CLEAR and move.weather_start != self.state.weather:
            self.state.weather = move.weather_start
        if move.field_start != Terrain.NONE and move.field_start != self.state.field:
            self.state.field = move.field_start
        if move.toggle_trickroom and not self.state.trickroom:
            self.state.trickroom = True
        # side conditions changes
        if move.toggle_lightscreen and not self.state.sides[side].lightscreen:
            self.state.sides[side].lightscreen = True
        if move.toggle_reflect and not self.state.sides[side].reflect:
            self.state.sides[side].reflect = True
        if move.toggle_tailwind and not self.state.sides[side].tailwind:
            self.state.sides[side].tailwind = True
        if move.hazard == Hazard.STEALTH_ROCK:
            self.state.sides[side].stealth_rock = True
        if move.hazard == Hazard.TOXIC_SPIKES:
            self.state.sides[side].toxic_spikes = True
        # Pokemon effects
        if move.heal > 0:
            attacker.recover(int(damage * move.heal))
        if move.recoil > 0:
            attacker.deal_damage(int(damage * move.recoil))
        if move.force_switch:
            pass  # TODO
        if move.self_switch:
            pass  # TODO
        if move.change_type:
            attacker.types = [attacker.battling_moves[0].constants.pkm_type]
        if any(b > 0 for b in move.boosts):
            attacker.boosts = [_b + b for _b, b in zip(attacker.boosts, move.boosts)]
        if move.protect:
            attacker.protect = True

    def _perform_target_effects(self,
                               move: Move,
                               defender: BattlingPokemon):
        # Pokemon effects
        if move.status != Status.NONE and defender.status == Status.NONE:
            defender.status = move.status
        # Move Effects
        if move.disable and not any(
                m.disabled for m in defender.battling_moves) and defender.last_used_move is not None:
            defender.last_used_move.disabled = True

    def _on_fainted(self, pkm: BattlingPokemon):
        side: int
        if self.state.sides[side].team_fainted():
            raise BattleEngine.TeamFainted()
        self._perform_switches()

    def _on_switch(self, pkm: BattlingPokemon):
        # hazzards
        pass