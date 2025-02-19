from itertools import product

from numpy import argmax
from numpy.random import choice

from vgc2.agent import BattlePolicy
from vgc2.battle_engine import State, BattleCommand, calculate_damage, BattleRuleParam


class RandomBattlePolicy(BattlePolicy):
    """
    Policy that selects moves and switches randomly. Tailored for single and double battles.
    """

    def __init__(self,
                 switch_prob: float = .15):
        self.switch_prob = switch_prob

    def decision(self,
                 state: State) -> list[BattleCommand]:
        team = state.sides[0].team
        n_switches = len(team.reserve)
        n_targets = len(state.sides[1].team.active)
        cmds: list[BattleCommand] = []
        for pkm in team.active:
            n_moves = len(pkm.battling_moves)
            switch_prob = 0 if n_switches == 0 else self.switch_prob
            action = choice(n_moves + 1, p=[switch_prob] + [(1. - switch_prob) / n_moves] * n_moves) - 1
            if action >= 0:
                target = choice(n_targets, p=[1 / n_targets] * n_targets)
            else:
                target = choice(n_switches, p=[1 / n_switches] * n_switches)
            cmds += [(action, target)]
        return cmds


def greedy_single_battle_decision(params: BattleRuleParam,
                                  state: State) -> list[BattleCommand]:
    attacker, defender = state.sides[0].team.active[0], state.sides[1].team.active[0]
    outcomes = [calculate_damage(params, 0, move.constants, state, attacker, defender)
                if move.pp > 0 and not move.disabled else 0 for move in attacker.battling_moves]
    return [(int(argmax(outcomes)), 0) if outcomes else (0, 0)]


def greedy_double_battle_decision(params: BattleRuleParam,
                                  state: State) -> list[BattleCommand]:
    attackers, defenders = state.sides[0].team.active, state.sides[1].team.active
    strategies = []
    for sources in product(list(range(len(attackers[0].battling_moves))),
                           list(range(len(attackers[1].battling_moves))) if len(attackers) > 1 else []):
        for targets in product(list(range(len(defenders))), list(range(len(defenders)))):
            damage, ko, hp = 0, 0, [d.hp for d in defenders]
            for i, (source, target) in enumerate(zip(sources, targets)):
                attacker, defender, move = attackers[i], defenders[target], attackers[i].battling_moves[source]
                if move.pp == 0 or move.disabled:
                    continue
                new_hp = max(0, hp[target] - calculate_damage(params, 0, move.constants, state, attacker, defender))
                damage += hp[target] - new_hp
                ko += int(new_hp == 0)
                hp[target] = new_hp
            strategies += [(ko, damage, sources, targets)]
    if len(strategies) == 0:
        return [(choice(len(a.battling_moves)), choice(len(defenders))) for a in attackers]
    best = max(strategies, key=lambda x: 1000 * x[0] + x[1])
    return list(zip(best[2], best[3]))


class GreedyBattlePolicy(BattlePolicy):
    """
    Greedy strategy that prioritizes KOs and damage output with only one turn lookahead. Performs no switches.
    """

    def __init__(self,
                 params: BattleRuleParam = BattleRuleParam()):
        self.params = params

    def decision(self, state: State) -> list[BattleCommand]:
        n_active_0, n_active_1 = len(state.sides[0].team.active), len(state.sides[1].team.active)
        match max(n_active_0, n_active_1):
            case 1:
                return greedy_single_battle_decision(self.params, state)
            case 2:
                return greedy_double_battle_decision(self.params, state)


def select(max_action: int):
    while True:
        try:
            act = int(input('Select Action: '))
            if 0 < act < max_action:
                return act
            else:
                print('Invalid action. Select again.')
        except:
            print('Invalid action. Select again.')


class TerminalBattle(BattlePolicy):
    """
    Terminal battle interface. Tailored for single and double battles.
    """

    def decision(self,
                 state: State) -> list[BattleCommand]:
        cmds: list[BattleCommand] = []
        team = state.sides[0].team
        print('~ Actions ~')
        for pkm in team.active:
            print(pkm)
            n_moves = len(pkm.battling_moves)
            n_switches = len(team.reserve)
            for i, move in enumerate(pkm.battling_moves):
                print(i, '->', move)
            for i, r_pkm in enumerate(team.reserve):
                print(i + n_moves, '-> Switch to', r_pkm)
            act = select(n_moves + n_switches)
            targets = state.sides[1].team.active
            if 0 < act < n_moves and len(targets) > 1:
                print('~ Targets ~')
                for i, a in enumerate(targets):
                    print(i, '-> ', a)
                cmds += [(act, select(len(targets)))]
            else:
                cmds += [(-1, act - n_moves)]
        print()
        return cmds
