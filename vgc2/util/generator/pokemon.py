from numpy import clip
from numpy.random import normal, rand, choice, multinomial

from vgc2.agent.policies import Roster
from vgc2.pkm_engine.move import Move
from vgc2.pkm_engine.nature import Nature
from vgc2.pkm_engine.pokemon import PokemonSpecies, Pokemon
from vgc2.pkm_engine.typing import Type
from vgc2.util.generator.move import gen_move_subset


def gen_pkm_species(moves: list[Move],
                    n_moves: int = 4) -> PokemonSpecies:
    n_types = 1 if rand() < 0.5 else 2
    return PokemonSpecies(
        base_stats=(
            clip(int(normal(120, 0.2, 1)[0]), 0, 160),
            clip(int(normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(normal(100, 0.2, 1)[0]), 0, 140),
            clip(int(normal(100, 0.2, 1)[0]), 0, 140)
        ),
        types=[Type(x) for x in choice(len(Type), 2, False)],
        moves=gen_move_subset(n_moves, moves)
    )


def gen_pkm(species: PokemonSpecies, max_moves: int = 4) -> Pokemon:
    n_moves = len(species.moves)
    return Pokemon(
        species=species,
        move_indexes=list(choice(n_moves, min(max_moves, n_moves), False)),
        level=100,
        ivs=(31,) * 6,
        evs=tuple(multinomial(510, [1 / 6] * 6, size=1)[0]),
        nature=Nature(choice(len(Nature), 1, False))
    )


def gen_pkm_roster(n: int,
                   moves: list[Move],
                   n_moves: int = 4) -> Roster:
    roster: Roster = []
    i = 0
    while i < n:
        roster += [gen_pkm_species(moves, n_moves)]
        i += 1
    return roster
