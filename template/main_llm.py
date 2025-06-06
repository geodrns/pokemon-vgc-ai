import argparse
from competitor_llm import LLM_Competitor
from vgc2.net.server import RemoteCompetitorManager, BASE_PORT

def main(_args):
    _id = _args.id
    competitor = LLM_Competitor(name=f"LLM_Competitor {_id}")
    server = RemoteCompetitorManager(competitor, port=BASE_PORT + _id, authkey=f'Competitor {_id}'.encode('utf-8'))
    server.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, default=0)
    args = parser.parse_args()
    main(args)
