from vgc2.agent import BattlePolicy, TeamSelectionPolicy, TeamBuildPolicy
from vgc2.agent.BattlePolicies import RandomPlayer, TerminalPlayer
from vgc2.agent.TeamBuildPolicies import TerminalTeamBuilder, RandomTeamBuilder
from vgc2.agent.TeamSelectionPolicies import FirstEditionTeamSelectionPolicy
from vgc2.competition.competitor import Competitor


class ExampleCompetitor(Competitor):

    def __init__(self, name: str = "Example"):
        self._name = name
        self._battle_policy = RandomPlayer()
        self._team_selection_policy = FirstEditionTeamSelectionPolicy()
        self._team_build_policy = RandomTeamBuilder()

    @property
    def name(self):
        return self._name

    @property
    def team_build_policy(self) -> TeamBuildPolicy:
        return self._team_build_policy

    @property
    def selection_policy(self) -> TeamSelectionPolicy:
        return self._team_selection_policy

    @property
    def battle_policy(self) -> BattlePolicy:
        return self._battle_policy


class TerminalExampleCompetitor(ExampleCompetitor):

    def __init__(self, name: str = "TerminalPlayer"):
        super().__init__(name)
        self._battle_policy = TerminalPlayer()
        self._team_selection_policy = TeamSelectionPolicy()
        self._team_build_policy = TerminalTeamBuilder()

    @property
    def name(self):
        return self._name

    @property
    def team_build_policy(self) -> TeamBuildPolicy:
        return self._team_build_policy

    @property
    def selection_policy(self) -> TeamSelectionPolicy:
        return self._team_selection_policy

    @property
    def battle_policy(self) -> BattlePolicy:
        return self._battle_policy


"""
class GUIExampleCompetitor(ExampleCompetitor):

    def __init__(self, name: str = "GUIPlayer"):
        self._battle_policy = GUIPlayer()
        self._team_selection_policy = GUITeamSelection()
        self._team_build_policy = GUITeamBuilder()

    @property
    def name(self):
        return self._name

    @property
    def team_build_policy(self) -> TeamBuildPolicy:
        return self._team_build_policy

    @property
    def team_selection_policy(self) -> TeamSelectionPolicy:
        return self._team_selection_policy

    @property
    def battle_policy(self) -> BattlePolicy:
        return self._battle_policy
"""


