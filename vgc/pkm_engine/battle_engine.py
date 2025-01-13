from typing import List, Tuple

from gymnasium import Env

from vgc.pkm_engine.game_state import State, Side
from vgc.pkm_engine.modifiers import Weather, Terrain, Hazard, Status
from vgc.pkm_engine.move import Move
from vgc.pkm_engine.pokemon import Pokemon, BattlingPokemon

Team = List[Pokemon]
BattlingTeam = List[BattlingPokemon]


def battling_team(team: Team):
    return [BattlingPokemon(p) for p in team]


Action = Tuple[int, int]  # move, target


class BattleEngine:
    __slots__ = ('n_active', 'state')

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

    def __str__(self):
        return str(self.state)

    def reset(self):
        self.state.reset()

    def change_teams(self,
                     teams: Tuple[Team, Team]):
        battling_teams = (battling_team(teams[0]), battling_team(teams[1]))
        self.state.sides[0].active = battling_teams[0][:self.n_active]
        self.state.sides[0].reserve = battling_teams[0][self.n_active:]
        self.state.sides[1].active = battling_teams[1][:self.n_active]
        self.state.sides[1].reserve = battling_teams[1][self.n_active:]

    def run_turn(self,
                 actions: Tuple[List[Action], List[Action]]):
        self._perform_switches(actions)

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
            # hazard damage and add forced switch

    def _perform_move_effects(self,
                              move: Move,
                              side: int,
                              user: BattlingPokemon,
                              target: BattlingPokemon,
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
        if move.status != Status.NONE and target.status == Status.NONE:
            target.status = move.status
        if move.heal > 0:
            user.recover(int(damage * move.heal))
        if move.recoil > 0:
            user.deal_damage(int(damage * move.recoil))
        if move.force_switch:
            pass
        if move.self_switch:
            pass
        if move.change_type:
            user.types = [user.battling_moves[0].constants.pkm_type]
        if any(b > 0 for b in move.boosts):
            user.boosts = [_b + b for _b, b in zip(user.boosts, move.boosts)]
        if move.protect:
            user.protect = True
        # Move Effects
        if move.disable and not any(m.disabled for m in target.battling_moves) and target.last_used_move is not None:
            target.last_used_move.disabled = True


class BattleEnv(Env, BattleEngine):
    def __init__(self):
        super().__init__()
