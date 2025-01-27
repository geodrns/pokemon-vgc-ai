from vgc2.battle_engine.constants import DAMAGE_MULTIPLICATION_ARRAY, TERRAIN_DAMAGE_BOOST, BOOST_MULTIPLIER_LOOKUP
from vgc2.battle_engine.game_state import State
from vgc2.battle_engine.modifiers import Category, Weather, Terrain, Status, MutableStats
from vgc2.battle_engine.move import Move
from vgc2.battle_engine.pokemon import Stat, BattlingPokemon
from vgc2.battle_engine.typing import Type


def calculate_damage(attacking_side: int,
                     move: Move,
                     state: State,
                     attacker: BattlingPokemon,
                     defender: BattlingPokemon) -> int:
    # determine if combat is physical or special
    attacking_type = move.category
    if attacking_type == Category.PHYSICAL:
        attack = Stat.ATTACK
        defense = Stat.DEFENSE
    elif attacking_type == Category.SPECIAL:
        attack = Stat.SPECIAL_ATTACK
        defense = Stat.SPECIAL_DEFENSE
    else:
        return 0
    # determine if move has no base power
    if move.base_power == 0:
        return 0
    # calculate actual power of attacker and defender
    attacking_stats = calculate_boosted_stats(attacker)
    defending_stats = calculate_boosted_stats(defender)
    # rock types get 1.5x SPDEF in sand
    # ice types get 1.5x DEF in snow
    try:
        if state.weather == Weather.SAND and Type.ROCK in defender.types:
            defending_stats[Stat.SPECIAL_DEFENSE] = int(defending_stats[Stat.SPECIAL_DEFENSE] * 1.5)
        elif state.weather == Weather.SNOW and Type.ICE in defender.types:
            defending_stats[Stat.DEFENSE] = int(defending_stats[Stat.DEFENSE] * 1.5)
    except KeyError:
        pass
    # apply damage formula
    damage = int(int((2 * attacker.constants.level) / 5) + 2) * move.base_power
    damage = int(damage * attacking_stats[attack] / defending_stats[defense])
    damage = int(damage / 50) + 2
    damage *= calculate_modifier(attacker, defender, move, state, attacking_side)
    # result
    return damage


def calculate_boosted_stats(pkm: BattlingPokemon) -> MutableStats:
    return [
        0,
        BOOST_MULTIPLIER_LOOKUP[pkm.boosts[Stat.ATTACK]] * pkm.constants.stats[Stat.ATTACK],
        BOOST_MULTIPLIER_LOOKUP[pkm.boosts[Stat.DEFENSE]] * pkm.constants.stats[Stat.DEFENSE],
        BOOST_MULTIPLIER_LOOKUP[pkm.boosts[Stat.SPECIAL_ATTACK]] * pkm.constants.stats[Stat.SPECIAL_ATTACK],
        BOOST_MULTIPLIER_LOOKUP[pkm.boosts[Stat.SPECIAL_DEFENSE]] * pkm.constants.stats[Stat.SPECIAL_DEFENSE],
    ]


def calculate_modifier(attacker: BattlingPokemon,
                       defender: BattlingPokemon,
                       move: Move,
                       state: State,
                       attacking_side: int) -> float:
    modifier = 1
    modifier *= type_effectiveness_modifier(move.pkm_type, defender.types)
    modifier *= weather_modifier(move, state.weather)
    modifier *= stab_modifier(attacker, move)
    modifier *= burn_modifier(attacker, move)
    modifier *= terrain_modifier(move, state.field)
    modifier *= light_screen_modifier(move, state.sides[attacking_side].lightscreen)
    modifier *= reflect_modifier(move, state.sides[attacking_side].reflect)
    return modifier


def type_effectiveness_modifier(move_type: Type,
                                defending_types: list[Type]) -> float:
    modifier = 1
    for defending_pkm_type in defending_types:
        modifier *= DAMAGE_MULTIPLICATION_ARRAY[move_type][defending_pkm_type]
    return modifier


def weather_modifier(move: Move,
                     weather: Weather) -> float:
    if weather == Weather.CLEAR:
        return 1
    if weather == Weather.SUN and move.pkm_type == Type.FIRE:
        return 1.5
    elif weather == Weather.SUN and move.pkm_type == Type.WATER:
        return 0.5
    elif weather == Weather.RAIN and move.pkm_type == Type.WATER:
        return 1.5
    elif weather == Weather.RAIN and move.pkm_type == Type.FIRE:
        return 0.5
    return 1


def stab_modifier(attacker: BattlingPokemon,
                  move: Move) -> float:
    return 1.5 if move.pkm_type in [t for t in attacker.types] else 1


def burn_modifier(attacker: BattlingPokemon,
                  move: Move):
    return 0.5 if Status.BURN == attacker.status and move.category == Category.PHYSICAL else 1


def light_screen_modifier(move: Move,
                          light_screen: bool) -> float:
    return 0.5 if light_screen and move.category == Category.SPECIAL else 1


def reflect_modifier(move: Move,
                     reflect: bool) -> float:
    return 0.5 if reflect and move.category == Category.PHYSICAL else 1


def terrain_modifier(move: Move,
                     terrain: Terrain) -> float:
    if terrain == Terrain.NONE:
        return 1
    if terrain == Terrain.ELECTRIC_TERRAIN and move.pkm_type == Type.ELECTRIC:
        return TERRAIN_DAMAGE_BOOST
    elif terrain == Terrain.GRASSY_TERRAIN and move.pkm_type == Type.GRASS:
        return TERRAIN_DAMAGE_BOOST
    elif terrain == Terrain.MISTY_TERRAIN and move.pkm_type == Type.DRAGON:
        return 0.5
    elif terrain == Terrain.PSYCHIC_TERRAIN and move.pkm_type == Type.PSYCHIC:
        return TERRAIN_DAMAGE_BOOST
    elif terrain == Terrain.PSYCHIC_TERRAIN and move.priority > 0:
        return 0
    return 1


def calculate_stealth_rock_damage(pkm: BattlingPokemon) -> int:
    return pkm.constants.species.base_stats[Stat.MAX_HP] * 0.125 * type_effectiveness_modifier(Type.ROCK, pkm.types)


def calculate_poison_damage(pkm: BattlingPokemon) -> int:
    return pkm.constants.species.base_stats[Stat.MAX_HP] * 0.125


def calculate_burn_damage(pkm: BattlingPokemon) -> int:
    return pkm.constants.species.base_stats[Stat.MAX_HP] * 0.0625


def calculate_sand_damage(pkm: BattlingPokemon) -> int:
    for t in pkm.types:
        if t in (Type.ROCK, Type.GROUND, Type.STEEL):
            return 0
    return pkm.constants.species.base_stats[Stat.MAX_HP] * 0.125
