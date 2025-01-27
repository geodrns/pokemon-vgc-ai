from vgc2.balance.meta import MetaData
from vgc2.datatypes.Constants import DEFAULT_MATCH_N_BATTLES
from vgc2.datatypes.Objects import PkmRoster
from vgc2.util.generator.PkmTeamGenerators import RandomTeamFromRoster

from vgc2.competition import legal_team, CompetitorManager
from vgc2.ecosystem.BattleEcosystem import BattleEcosystem, Strategy


class ChampionshipEcosystem:

    def __init__(self, roster: PkmRoster, meta_data: MetaData, debug=False, render=False,
                 n_battles=DEFAULT_MATCH_N_BATTLES, strategy: Strategy = Strategy.RANDOM_PAIRING):
        self.meta_data = meta_data
        self.roster = roster
        self.rand_gen = RandomTeamFromRoster(self.roster)
        self.league: BattleEcosystem = BattleEcosystem(self.meta_data, debug, render, n_battles, strategy,
                                                       update_meta=True)
        self.debug = debug
        self.roster_ver = 0

    def register(self, cm: CompetitorManager):
        self.league.register(cm)

    def run(self, n_epochs: int, n_league_epochs: int):
        epoch = 0
        self.__reveal_roster_for_competitors()
        while epoch < n_epochs:
            print('Round', epoch + 1)
            if self.debug:
                print("TEAM BUILD\n")
            for cm in self.league.competitors:
                self.__set_new_team(cm)
                if self.debug:
                    print(cm.competitor.name)
                    print(cm.team)
                    print()
            if self.debug:
                print("LEAGUE\n")
            self.league.run(n_league_epochs)
            epoch += 1

    def __reveal_roster_for_competitors(self):
        for cm in self.league.competitors:
            try:
                cm.competitor.team_build_policy.set_roster(self.roster, self.roster_ver)
            except:
                print('ups 1')
                pass

    def __set_new_team(self, cm: CompetitorManager):
        try:
            cm.team = cm.competitor.team_build_policy.get_action(self.meta_data).get_copy()
            if not legal_team(cm.team, self.roster):
                print('ups 2')
                cm.team = self.rand_gen.get_team()
        except:
            print('ups 3')
            cm.team = cm.team if cm.team is not None else self.rand_gen.get_team()

    def strongest(self) -> CompetitorManager:
        return max(self.league.competitors, key=lambda c: c.elo)
