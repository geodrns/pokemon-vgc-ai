from numpy.random import choice

from vgc2.agent import BattlePolicy
from vgc2.battle_engine import State, BattleCommand


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
            action = choice(n_moves + 1, p=[self.switch_prob] + [(1. - self.switch_prob) / n_moves] * n_moves) - 1
            if action >= 0:
                target = choice(n_targets, p=[1 / n_targets] * n_targets)
            else:
                target = choice(n_switches, p=[1 / n_switches] * n_switches)
            cmds += [(action, target)]
        return cmds


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
