from Example_Competitor import ExampleCompetitor
from vgc2.competition.Competition import TreeChampionship
from vgc2.competition.competitor import CompetitorManager
from vgc2.datatypes.Objects import PkmRoster
from vgc2.util.generator.PkmRosterGenerators import RandomPkmRosterGenerator
from vgc2.util.generator.PkmTeamGenerators import RandomTeamGenerator

N_COMPETITORS = 16


def main():
    roster = None  # RandomPkmRosterGenerator().gen_roster()
    competitors = [ExampleCompetitor('Player ' + str(i)) for i in range(N_COMPETITORS)]
    championship = TreeChampionship(roster, debug=True, gen=RandomTeamGenerator(2))
    for competitor in competitors:
        championship.register(CompetitorManager(competitor))
    championship.new_tournament()
    winner = championship.run()
    print(winner.competitor.name + " wins the tournament!")


if __name__ == '__main__':
    main()
