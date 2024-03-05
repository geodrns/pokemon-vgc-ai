from vgc.behaviour import BattlePolicy, TeamSelectionPolicy
from vgc.behaviour.BattlePolicies import GUIPlayer, RandomPlayer, TerminalPlayer
from vgc.behaviour.TeamSelectionPolicies import TerminalTeamSelection, GUITeamSelection
from vgc.competition.Competitor import Competitor


class ExampleCompetitor(Competitor):

    def __init__(self, name: str = "Example"):
        self._name = name
        self._battle_policy = RandomPlayer()

    @property
    def name(self):
        return self._name

    @property
    def battle_policy(self) -> BattlePolicy:
        return self._battle_policy


class TerminalExampleCompetitor(ExampleCompetitor):

    def __init__(self, name: str = ""):
        super().__init__(name)

    @property
    def team_selection_policy(self) -> TeamSelectionPolicy:
        return TerminalTeamSelection()

    @property
    def battle_policy(self) -> BattlePolicy:
        return TerminalPlayer()


class GUIExampleCompetitor(ExampleCompetitor):

    def __init__(self, name: str = ""):
        super().__init__(name)

    @property
    def team_selection_policy(self) -> TeamSelectionPolicy:
        return GUITeamSelection()

    @property
    def battle_policy(self) -> BattlePolicy:
        return GUIPlayer()
