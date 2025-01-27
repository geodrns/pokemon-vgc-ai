from Example_Competitor import ExampleCompetitor
from vgc2.balance.meta import StandardMetaData
from vgc2.competition import CompetitorManager
from vgc2.ecosystem.BattleEcosystem import BattleEcosystem
from vgc2.util.generator.PkmRosterGenerators import RandomPkmRosterGenerator
from vgc2.util.generator.PkmTeamGenerators import RandomTeamFromRoster

N_PLAYERS = 16


def main():
    roster = RandomPkmRosterGenerator().gen_roster()
    meta_data = StandardMetaData()
    le = BattleEcosystem(meta_data, debug=True)
    for i in range(N_PLAYERS):
        cm = CompetitorManager(ExampleCompetitor("Player %d" % i))
        cm.team = RandomTeamFromRoster(roster).get_team()
        le.register(cm)
    le.run(10)


if __name__ == '__main__':
    main()
