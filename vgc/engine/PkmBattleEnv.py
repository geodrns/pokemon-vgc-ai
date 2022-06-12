import random
from copy import deepcopy
from multiprocessing.connection import Client
from typing import List, Tuple

import gym
import numpy as np
from gym import spaces

from vgc.competition.StandardPkmMoves import Struggle
from vgc.datatypes.Constants import DEFAULT_PKM_N_MOVES, MAX_HIT_POINTS, STATE_DAMAGE, SPIKES_2, SPIKES_3, \
    TYPE_CHART_MULTIPLIER, DEFAULT_N_ACTIONS
from vgc.datatypes.Objects import PkmTeam, Pkm, GameState, Weather, null_pkm
from vgc.datatypes.Types import WeatherCondition, PkmEntryHazard, PkmType, PkmStatus, PkmStat, N_HAZARD_STAGES, \
    MIN_STAGE, MAX_STAGE
from vgc.util.Encoding import GAME_STATE_ENCODE_LEN, partial_encode_game_state


def set_moves(pkm: Pkm, prediction: Pkm):
    for i in range(len(pkm.moves)):
        if not pkm.moves[i].revealed:
            if prediction is not None:
                pkm.moves[i] = prediction.moves[i]
            else:
                pkm.moves[i] = null_pkm.moves[i]


def set_pkm(pkm: Pkm, prediction: Pkm):
    if pkm.revealed:
        set_moves(pkm, prediction)
    elif prediction is not None:
        pkm.type = prediction.type
        pkm.hp = prediction.hp
        set_moves(pkm, prediction)
    else:
        pkm.type = null_pkm.type
        pkm.hp = null_pkm.hp
        set_moves(pkm, null_pkm)


class PkmBattleEnv(gym.Env, GameState):

    def __init__(self, teams: Tuple[PkmTeam, PkmTeam], weather=Weather(), debug: bool = False, conn: Client = None,
                 encode: Tuple[bool, bool] = (True, True)):
        # random active pokemon
        super().__init__(teams, weather)
        self.__n_turns_no_clear = None
        self.__switched = [False, False]
        self.__turn = 0
        self.__move_view = self.__create_pkm_move_view()
        self.__debug = debug
        self.__log = ''
        self.__commands = []
        self.__conn = conn
        self.__game_state_view = [GameState((self.teams[0], self.teams[1]), self.weather),
                                  GameState((self.teams[1], self.teams[0]), self.weather)]
        self.__requires_encode = encode
        self.action_space = spaces.Discrete(DEFAULT_N_ACTIONS)
        self.observation_space = spaces.Discrete(GAME_STATE_ENCODE_LEN)
        self.winner = -1

    def __get_forward_env(self, player: int, prediction: PkmTeam = None):
        env = PkmBattleEnv((deepcopy(self.teams[0]), deepcopy(self.teams[1])), deepcopy(self.weather))
        env.__n_turns_no_clear = self.__n_turns_no_clear
        env.__turn = self.__turn
        env.winner = self.winner
        # hidde information and replace with prediction information
        opp_team: PkmTeam = env.__game_state_view[player].teams[1]
        set_pkm(opp_team.active, prediction.active)
        for i in range(len(opp_team.party)):
            set_pkm(opp_team.party[i], prediction.party[i])
        return env

    def step(self, actions):

        # Reset variables
        r = [0., 0.]
        t = [False, False]
        if self.__debug:
            self.__turn += 1
            self.__log = f'TURN {self.__turn}\n\n'
            self.__commands.append(('event', ['log', f'Turn {self.__turn}.']))

        # switch pkm
        self.__process_switch_pkms(actions)

        # set trainer attack order
        first, second = self.__get_attack_order(actions)
        first_team = self.teams[first]
        first_pkm = first_team.active
        second_team = self.teams[second]
        second_pkm = second_team.active

        # get entry hazard damage
        dmg_2_first = self.__get_entry_hazard_damage(first)
        dmg_2_second = self.__get_entry_hazard_damage(second)

        r[first] = (dmg_2_second - dmg_2_first) / MAX_HIT_POINTS
        r[second] = (dmg_2_first - dmg_2_second) / MAX_HIT_POINTS

        active_not_fainted = not (first_pkm.fainted() or second_pkm.fainted())

        # process all pre battle effects
        self.__process_pre_battle_effects()

        # confusion state damage
        dmg_2_first = self.__get_pre_combat_damage(first) if active_not_fainted else 0.
        dmg_2_second = self.__get_pre_combat_damage(second) if active_not_fainted else 0.

        first_confusion_damage = dmg_2_first > 0.
        second_confusion_damage = dmg_2_second > 0.

        r[first] += (dmg_2_second - dmg_2_first) / MAX_HIT_POINTS
        r[second] += (dmg_2_first - dmg_2_second) / MAX_HIT_POINTS

        active_not_fainted = not (first_pkm.fainted() or second_pkm.fainted())

        # battle
        first_can_attack = active_not_fainted and not first_pkm.paralyzed() and not first_pkm.asleep() and not \
            first_confusion_damage
        if self.__debug and not first_can_attack:
            self.__log += f'CANNOT MOVE: Trainer {first} cannot move\n'
            self.__commands.append(('event', ['log', f'Trainer {first} cannot move.']))
        dmg_2_second, hp_2_first = self.__perform_pkm_attack(first, actions[first]) if first_can_attack else (0., 0.)

        active_not_fainted = not (first_pkm.fainted() or second_pkm.fainted())

        second_can_attack = active_not_fainted and not second_pkm.paralyzed() and not second_pkm.asleep() and not \
            second_confusion_damage
        if self.__debug and not second_can_attack:
            self.__log += f'CANNOT MOVE: Trainer {second} cannot move\n'
            self.__commands.append(('event', ['log', f'Trainer {second} cannot move.']))
        dmg_2_first, hp_2_second = self.__perform_pkm_attack(second, actions[second]) if second_can_attack else (0., 0.)

        r[first] += (dmg_2_second + hp_2_first - dmg_2_first) / MAX_HIT_POINTS + float(second_pkm.fainted())
        r[second] += (dmg_2_first + hp_2_second - dmg_2_second) / MAX_HIT_POINTS + float(first_pkm.fainted())

        # get post battle effects damage
        dmg_2_first = self.__get_post_battle_damage(first) if first_can_attack else 0.
        dmg_2_second = self.__get_post_battle_damage(second) if second_can_attack else 0.

        r[first] += (dmg_2_second - dmg_2_first) / MAX_HIT_POINTS
        r[second] += (dmg_2_first - dmg_2_second) / MAX_HIT_POINTS

        # process all post battle effects
        self.__process_post_battle_effects()

        # switch fainted pkm
        dmg_2_first, dmg_2_second = self.__switch_fainted_pkm()

        r[first] += (dmg_2_second - dmg_2_first) / MAX_HIT_POINTS
        r[second] += (dmg_2_first - dmg_2_second) / MAX_HIT_POINTS

        # check if battle ended
        t[first] = first_team.fainted()
        t[second] = second_team.fainted()

        r[first] += float(t[first])
        r[second] += float(t[second])

        finished = t[0] or t[1]

        if finished:
            self.winner = 1 if t[0] else 0

            if self.__debug:
                outcome0 = 'Lost' if self.teams[0].fainted() else 'Won'
                outcome1 = 'Lost' if self.teams[1].fainted() else 'Won'
                self.__log += f'\nTrainer 0 {outcome0}\n'
                self.__log += f'Trainer 1 {outcome1}\n'
                self.__commands.append(('event', ['log', f'Trainer 0 {outcome0}.']))

        if self.__requires_encode[0]:
            s0 = []
            partial_encode_game_state(s0, self.__game_state_view[0])
        else:
            s0 = self.__get_forward_env(0)
        if self.__requires_encode[1]:
            s1 = []
            partial_encode_game_state(s1, self.__game_state_view[1])
        else:
            s1 = self.__get_forward_env(1)
        return [s0, s1], r, finished, None

    def reset(self):
        self.weather.condition = WeatherCondition.CLEAR
        self.weather.n_turns_no_clear = 0
        self.__turn = 0
        self.winner = -1
        self.__switched = [False, False]

        for team in self.teams:
            team.reset()

        if self.__debug:
            self.__log = 'Trainer 0\n' + str(self.teams[0])
            self.__log += '\nTrainer 1\n' + str(self.teams[1])
            del self.__commands[:]
            self.__commands.append(('init', [self.teams[0].active.type.value,
                                             self.teams[0].party[0].type.value,
                                             self.teams[0].party[1].type.value,
                                             self.teams[0].active.hp,
                                             self.teams[0].active.moves[0].power,
                                             self.teams[0].active.moves[1].power,
                                             self.teams[0].active.moves[2].power,
                                             self.teams[0].active.moves[3].power,
                                             self.teams[1].active.type.value,
                                             self.teams[1].party[0].type.value,
                                             self.teams[1].party[1].type.value,
                                             self.teams[1].active.hp]))

        if self.__requires_encode[0]:
            s0 = []
            partial_encode_game_state(s0, self.__game_state_view[0])
        else:
            s0 = self.__get_forward_env(0)
        if self.__requires_encode[1]:
            s1 = []
            partial_encode_game_state(s1, self.__game_state_view[1])
        else:
            s1 = self.__get_forward_env(1)
        return [s0, s1]

    def render(self, mode='console'):
        if mode == 'console':
            print(self.__log)
        elif mode == 'ux' and self.__conn is not None:
            while len(self.__commands) > 0:
                self.__conn.send(self.__commands.pop(0))

    def __process_switch_pkms(self, actions: List[int]):
        """
        Switch pkm if players chosen to do so.

        :param actions: players actions
        :return:
        """
        for i, team in enumerate(self.teams):
            pos = actions[i] - DEFAULT_PKM_N_MOVES
            if 0 <= pos < (team.size() - 1):
                if not team.party[pos].fainted():
                    new_active, old_active, _ = team.switch(pos)
                    self.__switched[i] = True
                    if self.__debug:
                        self.__log += f'SWITCH: Trainer {i} switches {old_active} with {new_active} in party\n'
                        self.__commands.append(('switch', [i, pos, new_active.hp,
                                                           new_active.moves[0].power,
                                                           new_active.moves[1].power,
                                                           new_active.moves[2].power,
                                                           new_active.moves[3].power]))
                elif self.__debug:
                    self.__log += f'SWITCH FAILED: Trainer {i} fails to switch\n'
                    self.__commands.append(('event', ['log', f'Trainer {i} fails to switch.']))
            elif self.__debug and pos >= (team.size() - 1):
                self.__log += f'INVALID SWITCH: Trainer {i} fails to switch\n'
                self.__commands.append(('event', ['log', f'Trainer {i} fails to switch.']))

    def __get_entry_hazard_damage(self, t_id: int) -> float:
        """
        Get triggered damage to be dealt to a switched pkm.

        :param: t_id: owner trainer
        :return: damage to first pkm, damage to second pkm
        """
        damage = 0.
        team = self.teams[t_id]
        pkm = team.active
        spikes = team.entry_hazard[PkmEntryHazard.SPIKES]

        # Spikes damage
        if spikes and pkm.type != PkmType.FLYING and self.__switched[t_id]:
            before_hp = pkm.hp
            pkm.hp -= STATE_DAMAGE if spikes <= 1 else SPIKES_2 if spikes == 2 else SPIKES_3
            pkm.hp = 0. if pkm.hp < 0. else pkm.hp
            damage = before_hp - pkm.hp
            self.__switched[t_id] = False
            if self.__debug and damage > 0.:
                self.__log += f'ENTRY HAZARD DAMAGE: {str(pkm)} takes {damage} entry hazard damage from spikes, ' \
                              f'hp reduces from {before_hp} to {pkm.hp}\n '
                self.__commands.append(('event', ['log', f'Trainer {team} takes {damage} damage from spikes.']))
                self.__commands.append(('event', ['hp', team, pkm.hp]))

        return damage

    def __process_pre_battle_effects(self):
        """
        Process all pre battle effects.

        """
        # for all trainers
        for i in range(len(self.teams)):

            team = self.teams[i]
            pkm = team.active

            # check if active pkm should be no more confused
            if team.confused:
                team.n_turns_confused += 1
                if random.uniform(0, 1) <= 0.5 or team.n_turns_confused == 4:
                    team.confused = False
                    team.n_turns_confused = 0
                    if self.__debug:
                        self.__log += f'STATUS: Trainer {i}\'s {str(pkm)} is no longer confused\n'
                        self.__commands.append(('event', ['log', f'Trainer {i} active is no longer confused.']))

            # check if active pkm should be no more asleep
            if pkm.asleep():
                pkm.n_turns_asleep += 1
                if random.uniform(0, 1) <= 0.5 or pkm.n_turns_asleep == 4:
                    pkm.status = PkmStatus.NONE
                    pkm.n_turns_asleep = 0
                    if self.__debug:
                        self.__log += f'STATUS: Trainer {i}\'s {str(pkm)} is no longer asleep\n'
                        self.__commands.append(('event', ['log', f'Trainer {i} active is no longer asleep.']))

    def __process_post_battle_effects(self):
        """
        Process all post battle effects.

        """
        if self.weather.condition != WeatherCondition.CLEAR:
            self.__n_turns_no_clear += 1

            # clear weather if appropriated
            if self.__n_turns_no_clear > 5:
                self.weather.condition = WeatherCondition.CLEAR
                self.__n_turns_no_clear = 0
                if self.__debug:
                    self.__log += 'STATE: The weather is clear\n'
                    self.__commands.append(('event', ['log', f'The weather is clear.']))

    def __get_post_battle_damage(self, t_id: int) -> float:
        """
        Get triggered damage to be dealt to switched pkm.

        :param: t_id: owner trainer
        :return: damage to pkm
        """
        pkm = self.teams[t_id].active
        state_damage = 0.

        if self.weather.condition == WeatherCondition.SANDSTORM and (
                pkm.type != PkmType.ROCK and pkm.type != PkmType.GROUND and pkm.type != PkmType.STEEL):
            state_damage = STATE_DAMAGE
        elif self.weather.condition == WeatherCondition.HAIL and (pkm.type != PkmType.ICE):
            state_damage = STATE_DAMAGE

        before_hp = pkm.hp
        pkm.hp -= state_damage
        pkm.hp = 0. if pkm.hp < 0. else pkm.hp
        damage = before_hp - pkm.hp

        if self.__debug and state_damage > 0.:
            self.__log += 'STATE DAMAGE: %s takes %s weather damage from sandstorm/hail hp reduces from %s to %s\n' % (
                str(pkm), damage, before_hp, pkm.hp)
            self.__commands.append(('event', ['log', f'Trainer {t_id} takes {damage} damage from sandstorm/hail.']))
            self.__commands.append(('event', ['hp', t_id, pkm.hp]))

        if pkm.status == PkmStatus.POISONED or pkm.status == PkmStatus.BURNED:
            state_damage = STATE_DAMAGE

            before_hp = pkm.hp
            pkm.hp -= state_damage
            pkm.hp = 0. if pkm.hp < 0. else pkm.hp
            damage = before_hp - pkm.hp

            if self.__debug and damage > 0.:
                self.__log += 'STATE DAMAGE: %s takes %s state damage from %s, hp reduces from %s to %s\n' % (
                    str(pkm), damage, 'poison' if pkm.status == PkmStatus.POISONED else 'burn', before_hp, pkm.hp)
                self.__commands.append(('event', ['log', f'Trainer {t_id} takes {damage} damage from poison/burn.']))
                self.__commands.append(('event', ['hp', t_id, pkm.hp]))

        return damage

    def __get_attack_order(self, actions) -> Tuple[int, int]:
        """
        Get attack order for this turn.
        Priority is given to the pkm with highest speed_stage. Otherwise random.

        :return: tuple with first and second trainer to perform attack
        """
        action0 = actions[0]
        action1 = actions[1]
        speed0 = self.teams[0].stage[PkmStat.SPEED] + (
            self.teams[0].active.moves[action0].priority if action0 < DEFAULT_PKM_N_MOVES else 0)
        speed1 = self.teams[1].stage[PkmStat.SPEED] + (
            self.teams[1].active.moves[action1].priority if action1 < DEFAULT_PKM_N_MOVES else 0)
        if speed0 > speed1:
            order = [0, 1]
        elif speed1 < speed0:
            order = [1, 0]
        else:
            # random attack order
            order = [0, 1]
            np.random.shuffle(order)
        return order[0], order[1]

    class PkmMoveView:

        def __init__(self, engine):
            self.__engine = engine
            self._damage: float = 0.
            self._recover: float = 0.
            self._team: List[PkmTeam] = []
            self._active: List[Pkm] = []

        def set_weather(self, weather: WeatherCondition):
            if weather != self.__engine.weather.condition:
                self.__engine.weather.condition = weather
                self.__engine.__n_turns_no_clear = 0
                if self.__engine.__debug:
                    self.__engine.__log += f'STATE: The weather is now {weather.name}\n'
                    self.__engine.__commands.append(('event', ['log', f'The weather is now {weather.name}.']))

        def set_fixed_damage(self, damage: float):
            self._damage = damage

        def set_recover(self, recover: float):
            self._recover = recover

        def set_status(self, status: PkmStatus, t_id: int = 1):
            pkm = self._active[t_id]
            team = self._team[t_id]
            if status == PkmStatus.PARALYZED and pkm.type != PkmType.ELECTRIC and pkm.type != PkmType.GROUND and \
                    pkm.status != PkmStatus.PARALYZED:
                pkm.status = PkmStatus.PARALYZED
                if self.__engine.__debug:
                    self.__engine.__log += f'STATUS: {str(pkm)} was paralyzed\n'
                    self.__engine.__commands.append(('event', ['log', f'Trainer {t_id} is now paralyzed.']))
            elif status == PkmStatus.POISONED and pkm.type != PkmType.POISON and pkm.type != PkmType.STEEL and \
                    pkm.status != PkmStatus.POISONED:
                pkm.status = PkmStatus.POISONED
                if self.__engine.__debug:
                    self.__engine.__log += f'STATUS: {str(pkm)} was poisoned\n'
                    self.__engine.__commands.append(('event', ['log', f'Trainer {t_id} is now poisoned.']))
            elif status == PkmStatus.SLEEP and pkm.status != PkmStatus.SLEEP:
                pkm.status = PkmStatus.SLEEP
                pkm.n_turns_asleep = 0
                if self.__engine.__debug:
                    self.__engine.__log += f'STATUS: {str(pkm)} is now asleep\n'
                    self.__engine.__commands.append(('event', ['log', f'Trainer {t_id} is now asleep.']))
            elif not team.confused:
                team.confused = True
                if self.__engine.__debug:
                    self.__engine.__log += f'STATUS: {str(pkm)} is now confused\n'
                    self.__engine.__commands.append(('event', ['log', f'Trainer {t_id} is now confused.']))

        def set_stage(self, stat: PkmStat = PkmStat.ATTACK, delta_stage: int = 1, t_id: int = 1):
            if delta_stage != 0:
                team = self._team[t_id]
                if MIN_STAGE < team.stage[stat] < MAX_STAGE:
                    team.stage[stat] += delta_stage
                    if team.stage[stat] < MIN_STAGE:
                        team.stage[stat] = MIN_STAGE
                    elif team.stage[stat] > MAX_STAGE:
                        team.stage[stat] = MAX_STAGE
                    if self.__engine.__debug:
                        self.__engine.__log += 'STAGE: %s %s %s\n' % (
                            str(team.active), stat.name, 'increased' if delta_stage > 0 else 'decreased')
                        self.__engine.__commands.append(('event', [stat.name, t_id, team.stage[stat]]))

        def set_entry_hazard(self, hazard: PkmEntryHazard = PkmEntryHazard.SPIKES, t_id: int = 1):
            team = self.__engine.teams[t_id]
            team.entry_hazard[hazard] += 1
            if team.entry_hazard[hazard] >= N_HAZARD_STAGES:
                team.entry_hazard[hazard] = N_HAZARD_STAGES - 1
            elif self.__engine.__debug:
                self.__engine.__log += f'ENTRY HAZARD: Trainer {t_id} gets spikes\n'
                self.__engine.__commands.append(('event', ['log', f'Trainer {t_id} gets spikes.']))

        @property
        def recover(self):
            return self._recover

        @property
        def damage(self):
            return self._damage

    def __get_fixed_damage(self) -> float:
        damage = self.__move_view.damage
        self.__move_view._damage = 0.
        return damage

    def __get_recover(self) -> float:
        recover = self.__move_view.recover
        self.__move_view._recover = 0.
        return recover

    def __create_pkm_move_view(self):
        return PkmBattleEnv.PkmMoveView(self)

    def __get_attack_dmg_rcvr(self, t_id: int, m_id: int) -> Tuple[float, float]:
        """
        Get damage and recover done by an attack m_id of active pkm of trainer t_id

        :param t_id: trainer of the active pkm
        :param m_id: move of the active pkm
        :return: damage, recover
        """

        team = self.teams[t_id]
        pkm = team.active
        move = pkm.moves[m_id]

        if move.pp > 0:
            move.pp -= 1
        else:
            move = Struggle

        if move.acc <= random.random():
            if self.__debug:
                self.__log += 'MOVE FAILS: Trainer %s with %s fails %s\n' % (t_id, str(pkm), str(move))
                self.__commands.append(('event', ['log', f'Trainer {t_id} active fails its move.']))
            return 0., 0.

        opp = not t_id
        opp_team = self.teams[opp]
        opp_pkm = opp_team.active

        if self.__debug:
            self.__log += 'MOVE: Trainer %s with %s uses %s\n' % (t_id, str(pkm), str(move))
            self.__commands.append(('attack', [t_id, move.type.value, move.power > 0.]))

        self.__move_view._team = [team, opp_team]
        self.__move_view._active = [pkm, opp_pkm]
        move.effect(self.__move_view)

        # set recover
        recover = self.__get_recover()

        # calculate damage
        fixed_damage = self.__get_fixed_damage()
        if fixed_damage > 0. and TYPE_CHART_MULTIPLIER[move.type][opp_pkm.type] > 0.:
            damage = fixed_damage
        else:
            stab = 1.5 if move.type == pkm.type else 1.
            if (move.type == PkmType.WATER and self.weather.condition == WeatherCondition.RAIN) or (
                    move.type == PkmType.FIRE and self.weather.condition == WeatherCondition.SUNNY):
                weather = 1.5
            elif (move.type == PkmType.WATER and self.weather.condition == WeatherCondition.SUNNY) or (
                    move.type == PkmType.FIRE and self.weather.condition == WeatherCondition.RAIN):
                weather = .5
            else:
                weather = 1.
            stage_level = team.stage[PkmStat.ATTACK] - opp_team.stage[PkmStat.DEFENSE]
            stage = (stage_level + 2.) / 2 if stage_level >= 0. else 2. / (np.abs(stage_level) + 2.)
            multiplier = TYPE_CHART_MULTIPLIER[move.type][opp_pkm.type] if move != Struggle else 1.0
            damage = multiplier * stab * weather * stage * move.power

        return round(damage), round(recover)

    def __perform_pkm_attack(self, t_id: int, m_id: int) -> Tuple[float, float]:
        """
        Perform a pkm attack

        :param t_id: trainer
        :param m_id: move
        :return: reward, recover
        """
        damage, recover = 0., 0.

        if m_id < DEFAULT_PKM_N_MOVES:
            opponent = not t_id
            pkm = self.teams[t_id].active
            before_hp = pkm.hp
            opp_pkm = self.teams[opponent].active
            before_opp_hp = opp_pkm.hp

            # get damage and recover values from attack
            damage_2_deal, health_2_recover = self.__get_attack_dmg_rcvr(t_id, m_id)

            # perform recover
            pkm.hp += health_2_recover
            pkm.hp = MAX_HIT_POINTS if pkm.hp > MAX_HIT_POINTS else pkm.hp
            recover = pkm.hp - before_hp
            if self.__debug and recover > 0.:
                self.__log += f'RECOVER: recovers {recover}\n'
                self.__commands.append(('event', ['log', f'Trainer {t_id} active recovers.']))
                self.__commands.append(('event', ['hp', t_id, pkm.hp]))
            elif self.__debug and recover < 0.:
                self.__log += f'RECOIL DAMAGE: gets {-recover} recoil damage\n'
                self.__commands.append(('event', ['log', f'Trainer {t_id} active takes recoil damage.']))
                self.__commands.append(('event', ['hp', t_id, pkm.hp]))

            # perform damage
            opp_pkm.hp -= damage_2_deal
            opp_pkm.hp = 0. if opp_pkm.hp < 0. else opp_pkm.hp
            damage = before_opp_hp - opp_pkm.hp
            if self.__debug and damage > 0.:
                self.__log += 'DAMAGE: deals %s damage, hp reduces from %s to %s for %s\n' % (
                    damage, before_opp_hp, opp_pkm.hp, str(opp_pkm))
                self.__commands.append(('event', ['log', f'Trainer {1 if opponent else 0} active takes damage.']))
                self.__commands.append(('event', ['hp', 1 if opponent else 0, opp_pkm.hp]))

        return damage, recover

    def __get_pre_combat_damage(self, t_id: int) -> float:
        """
        Check if trainer t_id active pkm is confused this turn and cannot move and take damage.

        :param t_id: trainer
        :return: 0. if not confused or damage to take if confused
        """
        return STATE_DAMAGE if self.teams[t_id].confused and random.uniform(0, 1) <= 0.33 else 0.

    def __switch_fainted_pkm(self) -> Tuple[float, float]:
        """
        Recursive damage dealt to fainted switched pkm, while faiting for entry hazard.

        :return: damage to pkm 0, damage to pkm 1
        """
        damage0, damage1 = 0., 0.
        self.__switched = [False, False]
        team0 = self.teams[0]
        team1 = self.teams[1]
        pkm0 = self.teams[0].active
        pkm1 = self.teams[1].active
        if pkm0.fainted():
            if self.__debug:
                self.__log += 'FAINTED: %s\n' % (str(pkm0))
                self.__commands.append(('event', ['log', f'Trainer 0 active fainted.']))
            new_active, _, pos = team0.switch(-1)
            if self.__debug:
                if pos != -1:
                    self.__commands.append(('switch', [0, pos, new_active.hp,
                                                       new_active.moves[0].power,
                                                       new_active.moves[1].power,
                                                       new_active.moves[2].power,
                                                       new_active.moves[3].power]))
        if pkm1.fainted():
            if self.__debug:
                self.__log += 'FAINTED: %s\n' % (str(pkm1))
                self.__commands.append(('event', ['log', f'Trainer 1 active fainted.']))
            new_active, _, pos = team1.switch(-1)
            if self.__debug:
                if pos != -1:
                    self.__commands.append(('switch', [1, pos, new_active.hp]))
        if not pkm0.fainted():
            damage0 = self.__get_entry_hazard_damage(0)
        if not pkm1.fainted():
            damage1 = self.__get_entry_hazard_damage(1)
        d0, d1 = 0., 0.
        if (pkm0.fainted() or pkm1.fainted()) and (not team0.fainted() and not team1.fainted()):
            d0, d1 = self.__switch_fainted_pkm()
        return damage0 + d0, damage1 + d1

    def close(self):
        if self.__conn is not None:
            self.__conn.close()
