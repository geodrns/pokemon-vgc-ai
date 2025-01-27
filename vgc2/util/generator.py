from random import sample
from typing import Callable

from numpy import clip
from numpy.random import default_rng, Generator

from vgc2.agent import Roster
from vgc2.battle_engine.modifiers import Category, Weather, Terrain, Hazard, Status
from vgc2.battle_engine.move import Move
from vgc2.battle_engine.nature import Nature
from vgc2.battle_engine.pokemon import PokemonSpecies, Pokemon
from vgc2.battle_engine.team import Team
from vgc2.battle_engine.typing import Type

MoveGenerator = Callable[[Generator], Move]
MoveSetGenerator = Callable[[int, Generator], list[Move]]
PokemonSpeciesGenerator = Callable[[list[Move], int, Generator], PokemonSpecies]
PokemonGenerator = Callable[[PokemonSpecies, int, Generator], Pokemon]
RosterGenerator = Callable[[int, list[Move], int, Generator], Roster]
TeamGenerator = Callable[[int, int, Generator], Team]
RosterTeamGenerator = Callable[[Roster, int, int, Generator], Team]

_rng = default_rng()


def gen_move(rng: Generator = _rng) -> Move:
    category = Category(rng.choice(len(Category), 1, False))
    base_power = 0 if category == Category.OTHER else clip(int(rng.normal(100, 0.2, 1)[0]), 0, 140)
    effect = rng.random() if category == Category.OTHER else -1
    return Move(
        pkm_type=Type(rng.choice(len(Type), 1, False)),
        base_power=base_power,
        accuracy=1. if rng.random() < .5 else rng.uniform(.5, 1.),
        max_pp=clip(int(rng.normal(10, 2, 1)[0]), 5, 20),
        category=category,
        priority=1 if rng.random() < .3 else 0,
        force_switch=0 <= effect < 1 / 17,
        self_switch=1 / 17 <= effect < 2 / 17,
        ignore_evasion=2 / 17 <= effect < 3 / 17,
        protect=3 / 17 <= effect < 4 / 17,
        boosts=tuple(rng.multinomial(2, [1 / 8.] * 8)) if 4 / 17 <= effect < 5 / 17 else (0,) * 8,
        heal=rng.random() / 2 if 5 / 17 <= effect < 6 / 17 else 0.,
        recoil=rng.random() / 2 if 6 / 17 <= effect < 7 / 17 else 0.,
        weather_start=Weather(rng.choice(len(Weather) - 1, 1)[0] + 1) if 7 / 17 <= effect < 8 / 17
        else Weather.CLEAR,
        field_start=Terrain(rng.choice(len(Terrain) - 1, 1)[0] + 1) if 8 / 17 <= effect < 9 / 17
        else Terrain.NONE,
        toggle_trickroom=9 / 17 <= effect < 10 / 17,
        change_type=10 / 17 <= effect < 11 / 17,
        toggle_reflect=11 / 17 <= effect < 12 / 17,
        toggle_lightscreen=12 / 17 <= effect < 13 / 17,
        toggle_tailwind=13 / 17 <= effect < 14 / 17,
        hazard=Hazard(rng.choice(len(Hazard) - 1, 1)[0] + 1) if 14 / 17 <= effect < 15 / 17 else Hazard.NONE,
        status=Status(rng.choice(len(Status) - 1, 1)[0] + 1) if 15 / 17 <= effect < 16 / 17 else Status.NONE,
        disable=16 / 17 <= effect < 1)


def gen_move_set(n: int, rng: Generator = _rng) -> list[Move]:
    return [gen_move(rng) for _ in range(n)]


def gen_move_subset(n: int,
                    moves: list[Move]) -> list[Move]:
    return sample(moves, min(n, len(moves)))


def gen_pkm_species(moves: list[Move],
                    n_moves: int = 4,
                    rng: Generator = _rng) -> PokemonSpecies:
    n_types = 1 if rng.random() < 0.5 else 2
    return PokemonSpecies(
        base_stats=(
            clip(int(rng.normal(120, 0.2, 1)[0]), 0, 160),
            clip(int(rng.normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(rng.normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(rng.normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(rng.normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(rng.normal(100, 0.2, 1)[0]), 0, 140)),
        types=[Type(x) for x in rng.choice(len(Type), n_types)],
        moves=gen_move_subset(n_moves, moves))


def gen_pkm(species: PokemonSpecies,
            max_moves: int = 4,
            rng: Generator = _rng) -> Pokemon:
    n_moves = len(species.moves)
    return Pokemon(
        species=species,
        move_indexes=list(rng.choice(n_moves, min(max_moves, n_moves))),
        level=100,
        ivs=(31,) * 6,
        evs=tuple(rng.multinomial(510, [1 / 6] * 6)),
        nature=Nature(rng.choice(len(Nature), 1)[0]))


def gen_pkm_roster(n: int,
                   moves: list[Move],
                   n_moves: int = 4,
                   rng: Generator = _rng) -> Roster:
    return [gen_pkm_species(moves, n_moves, rng) for _ in range(n)]


def gen_team(n: int,
             n_moves: int,
             rng: Generator = _rng) -> Team:
    return Team([gen_pkm(gen_pkm_species(gen_move_set(n_moves), n_moves, rng), n_moves, rng) for _ in range(n)])


def gen_team_from_roster(roster: Roster,
                         n: int,
                         n_moves: int,
                         rng: Generator = _rng) -> Team:
    return Team([gen_pkm(roster[i], n_moves, rng) for i in rng.choice(len(roster), n)])
