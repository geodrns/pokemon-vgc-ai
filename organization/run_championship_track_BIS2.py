import argparse
from multiprocessing.connection import Client

from vgc2.competition import CompetitorManager
from vgc2.competition.ecosystem import Championship, Strategy, label_roster
from vgc2.meta import BasicMeta
from vgc2.net.client import ProxyCompetitor
from vgc2.net.server import BASE_PORT
from vgc2.util.generator import gen_move_set, gen_pkm_roster

def main(_args):
    move_set = gen_move_set(_args.n_moves)
    roster   = gen_pkm_roster(_args.roster_size, move_set)
    label_roster(move_set, roster)
    meta = BasicMeta(move_set, roster)

    # montamos el campeonato igual que en run_championship_track.py
    champ = Championship(
        roster, meta,
        _args.epochs,
        _args.n_active,
        _args.n_battles,
        _args.max_team_size,
        _args.max_pkm_moves,
        Strategy.ELO_PAIRING
    )
    conns = []
    for i in range(_args.n_agents):
        addr = ("localhost", _args.base_port + i)
        conn = Client(addr, authkey=f"Competitor {i}".encode())
        conns.append(conn)
        champ.register(CompetitorManager(ProxyCompetitor(conn)))

    champ.run()
    ranking = champ.ranking()

    # imprimimos TODO el ranking
    for pos, entry in enumerate(ranking, start=1):
        name = entry.competitor.name
        elo  = entry.elo
        print(f"{pos:2d}. {name:20s}  ELO {elo:.2f}")

    for c in conns:
        c.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n_agents",      type=int, default=2)
    p.add_argument("--base_port",     type=int, default=6000)
    p.add_argument("--epochs",        type=int, default=10)
    p.add_argument("--n_moves",       type=int, default=100)
    p.add_argument("--roster_size",   type=int, default=50)
    p.add_argument("--max_team_size", type=int, default=3)
    p.add_argument("--n_active",      type=int, default=2)
    p.add_argument("--max_pkm_moves", type=int, default=4)
    p.add_argument("--n_battles",     type=int, default=3)
    args = p.parse_args()
    main(args)
