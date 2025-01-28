from vgc2.agent.battle import RandomBattlePolicy
from vgc2.battle_engine import TeamView, BattleEngine
from vgc2.competition.match import run_battle
from vgc2.util.generator import gen_team


def main():
    for _ in range(100000):
        team = gen_team(4, 4), gen_team(4, 4)
        view = TeamView(team[0]), TeamView(team[1])
        engine = BattleEngine(2)
        engine.set_teams(team, view)
        agent = RandomBattlePolicy(), RandomBattlePolicy()
        winner = run_battle(engine, agent)
        print("~ Team 0 ~")
        print(team[0])
        print("~ Team 1 ~")
        print(team[1])
        print("Side " + str(winner) + " wins!")


if __name__ == '__main__':
    main()
