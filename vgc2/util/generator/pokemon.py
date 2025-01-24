from typing import Callable

from numpy import clip
from numpy.random import Generator

from vgc2.agent.policies import Roster
from vgc2.pkm_engine.move import Move
from vgc2.pkm_engine.nature import Nature
from vgc2.pkm_engine.pokemon import PokemonSpecies, Pokemon
from vgc2.pkm_engine.typing import Type
from vgc2.util.generator.move import gen_move_subset, _rng

PokemonSpeciesGenerator = Callable[[list[Move], int, Generator], PokemonSpecies]
PokemonGenerator = Callable[[PokemonSpecies, int, Generator], Pokemon]
RosterGenerator = Callable[[int, list[Move], int, Generator], Roster]


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
