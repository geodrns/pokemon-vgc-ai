from typing import Callable

from numpy.random import Generator

from vgc2.agent.policies import Roster
from vgc2.pkm_engine.team import Team
from vgc2.util.generator.move import gen_move_set, _rng
from vgc2.util.generator.pokemon import gen_pkm, gen_pkm_species

TeamGenerator = Callable[[int, int, Generator], Team]
RosterTeamGenerator = Callable[[Roster, int, int, Generator], Team]


def gen_team(n: int,
             n_moves: int,
             rng: Generator = _rng) -> Team:
    return Team([gen_pkm(gen_pkm_species(gen_move_set(n_moves), n_moves, rng), n_moves, rng) for _ in range(n)])


def gen_team_from_roster(roster: Roster,
                         n: int,
                         n_moves: int,
                         rng: Generator = _rng) -> Team:
    return Team([gen_pkm(roster[i], n_moves, rng) for i in rng.choice(len(roster), n)])
