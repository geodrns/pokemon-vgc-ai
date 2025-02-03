from vgc2.agent.battle import RandomBattlePolicy
from vgc2.battle_engine import BattleEngine
from vgc2.competition.match import run_battle
from vgc2.util.generator import gen_team


def main():
    team = gen_team(4, 4), gen_team(4, 4)
    engine = BattleEngine(2)
    engine.set_teams(team)
    agent = RandomBattlePolicy(), RandomBattlePolicy()
    print("~ Team 0 ~")
    print(team[0])
    print("~ Team 1 ~")
    print(team[1])
    winner = run_battle(engine, agent)
    print("Side " + str(winner) + " wins!")


if __name__ == '__main__':
    main()
