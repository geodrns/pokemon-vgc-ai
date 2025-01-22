from vgc2.balance.meta import StandardMetaData
from vgc2.agent.TeamBuildPolicies import RandomTeamBuilder
from vgc2.util.generator.PkmRosterGenerators import RandomPkmRosterGenerator


def main():
    roster = RandomPkmRosterGenerator().gen_roster()
    for pt in roster:
        print(pt)
    a = RandomTeamBuilder()
    a.set_roster(roster)
    t = a.get_action(StandardMetaData())
    print(t)


if __name__ == '__main__':
    main()
