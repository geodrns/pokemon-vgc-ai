from vgc.pkm_engine.constants import ACCURACY_MULTIPLIER_LOOKUP
from vgc.pkm_engine.modifiers import Stat
from vgc.pkm_engine.move import BattlingMove
from vgc.pkm_engine.pokemon import BattlingPokemon


def move_hit_threshold(move: BattlingMove,
                       user: BattlingPokemon,
                       target: BattlingPokemon) -> float:
    return (move.constants.accuracy *
            ACCURACY_MULTIPLIER_LOOKUP[user.boosts[Stat.ACCURACY] - target.boosts[Stat.EVASION]])
