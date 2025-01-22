from numpy.random import choice

from vgc.agent.policies import BattlePolicy
from vgc.pkm_engine.battle_engine import BattleCommand
from vgc.pkm_engine.game_state import State


class RandomBattlePolicy(BattlePolicy):
    """
    Policy that selects moves and switches randomly. Tailored for single and double battles. Will avoid disabled and
    moves without PP. Will not make invalid targets.
    """

    def __init__(self, switch_prob: float = .15):
        self.switch_prob = switch_prob

    def decision(self, obs: State) -> list[BattleCommand]:
        team = obs.sides[0].team
        active = team.active
        n_reserve = sum(1 for x in team.reserve if not x.fainted())
        n_targets = len(obs.sides[1].team.active)
        commands: list[BattleCommand] = []
        for pkm in active:
            n_moves = max(1, len([x for x in pkm.battling_moves if x.pp > 0 and not x.disabled]))
            n_switches = max(1, n_reserve)
            switch_prob = 0 if n_reserve == 0 else self.switch_prob
            p = [(1. - switch_prob) / n_moves] * n_moves + [switch_prob / n_switches] * n_switches
            action = choice(n_moves + n_switches, p=p)
            if action < n_moves:
                target = choice(n_targets, p=[1 / n_targets] * n_targets)
            else:
                target = choice(n_switches, p=[1 / n_switches] * n_switches)
            commands += [(action, target)]
        return commands
