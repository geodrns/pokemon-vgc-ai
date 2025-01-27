import argparse
from multiprocessing.connection import Client

from vgc2.competition import CompetitorManager
from vgc2.competition.tournament import TreeTournament
from vgc2.network.proxy import ProxyCompetitor


def main(args):
    n_agents = args.n_agents
    conns = []
    cms = []
    for i in range(n_agents):
        address = ('localhost', args.base_port + i)
        conn = Client(address, authkey=f'Competitor {i}'.encode('utf-8'))
        conns.append(conn)
        cms += [CompetitorManager(ProxyCompetitor(conn))]
    tournament = TreeTournament(cms, max_team_size=args.max_team_size, max_pkm_moves=args.max_pkm_moves)
    tournament.build_tree()
    winner = tournament.run()
    print(winner.competitor.name + " wins the tournament!")
    for conn in conns:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_agents', type=int, default=2)
    parser.add_argument('--max_team_size', type=int, default=4)
    parser.add_argument('--n_active', type=int, default=2)
    parser.add_argument('--max_pkm_moves', type=int, default=4)
    parser.add_argument('--base_port', type=int, default=5000)
    args = parser.parse_args()
    main(args)
