from vgc.pkm_engine.constants import BOOST_MULTIPLIER_LOOKUP
from vgc.pkm_engine.game_state import State
from vgc.pkm_engine.modifiers import Status, Stat
from vgc.pkm_engine.move import Move
from vgc.pkm_engine.pokemon import BattlingPokemon


def paralysis_modifier(attacker: BattlingPokemon):
    return 0.5 if attacker.status == Status.PARALYZED else 1.0


def trickroom_modifier(state: State):
    return -1.0 if state.trickroom else 1.0


def boosted_speed(attacker):
    return BOOST_MULTIPLIER_LOOKUP[attacker.boosts[Stat.SPEED]] * attacker.constants.stats[Stat.SPEED]


def priority_calculator(move: Move,
                        attacker: BattlingPokemon,
                        state: State):
    return move.priority * 1000 + paralysis_modifier(attacker) * trickroom_modifier(state) * boosted_speed(attacker)
