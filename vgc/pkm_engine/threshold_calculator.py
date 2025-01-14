from vgc.pkm_engine.constants import ACCURACY_MULTIPLIER_LOOKUP
from vgc.pkm_engine.modifiers import Stat
from vgc.pkm_engine.move import BattlingMove
from vgc.pkm_engine.pokemon import BattlingPokemon


def move_hit_threshold(move: BattlingMove,
                       attacker: BattlingPokemon,
                       defender: BattlingPokemon) -> float:
    return (move.constants.accuracy *
            ACCURACY_MULTIPLIER_LOOKUP[attacker.boosts[Stat.ACCURACY] -
                                       (0 if move.constants.ignore_evasion else defender.boosts[Stat.EVASION])])


def thawed_threshold():
    return 0.2


def paralysis_threshold():
    return 0.25


def protect_threshold(move: BattlingMove,
                      target: BattlingPokemon) -> float:
    return move.constants.accuracy - target._consecutive_protect * 1/3
