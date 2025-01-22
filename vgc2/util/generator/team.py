from vgc2.agent.policies import Roster
from vgc2.pkm_engine.pokemon import Pokemon
from vgc2.pkm_engine.team import Team
from vgc2.util.generator.move import gen_move_set
from vgc2.util.generator.pokemon import gen_pkm, gen_pkm_species


def gen_team(n: int, n_moves: int) -> Team:
    members: list[Pokemon] = []
    i = 0
    while i < n:
        members += [gen_pkm(gen_pkm_species(gen_move_set(n_moves), n_moves), n_moves)]
        i += 1
    return Team(members)


def gen_team_from_roster(roster: Roster, n: int) -> Team:
    members: list[Pokemon] = []

    return Team(members)
