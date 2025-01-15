from vgc.pkm_engine.constants import ACCURACY_MULTIPLIER_LOOKUP
from vgc.pkm_engine.modifiers import Stat
from vgc.pkm_engine.move import Move
from vgc.pkm_engine.pokemon import BattlingPokemon


def accuracy_evasion_modifier(move: Move,
                              attacker: BattlingPokemon,
                              defender: BattlingPokemon) -> float:
    return ACCURACY_MULTIPLIER_LOOKUP[attacker.boosts[Stat.ACCURACY] -
                                      (0 if move.ignore_evasion else defender.boosts[Stat.EVASION])]


def protect_modifier(move: Move,
                     attacker: BattlingPokemon) -> float:
    return 1 / 3 ** attacker._consecutive_protect if move.protect else 1.0


def move_hit_threshold(move: Move,
                       attacker: BattlingPokemon,
                       defender: BattlingPokemon) -> float:
    return move.accuracy * accuracy_evasion_modifier(move, attacker, defender) * protect_modifier(move, attacker)


def thaw_threshold():
    return 0.2


def paralysis_threshold():
    return 0.25
