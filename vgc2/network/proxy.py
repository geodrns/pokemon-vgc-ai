from multiprocessing.connection import Client

from vgc2.agent import BattlePolicy, SelectionPolicy, SelectionCommand, TeamBuildPolicy, Roster, TeamBuildCommand, \
    MetaBalancePolicy, RosterBalanceCommand, RuleBalanceCommand, RuleBalancePolicy
from vgc2.battle_engine import State, BattleCommand, Team
from vgc2.competition import Competitor, DesignCompetitor
from vgc2.meta import Meta
from vgc2.meta.constraints import Constraints


class ProxyBattlePolicy(BattlePolicy):

    def __init__(self,
                 conn: Client):
        self.conn: Client = conn

    def decision(self,
                 state: State) -> list[BattleCommand]:
        self.conn.send(('BattlePolicy', state))
        return self.conn.recv()


class ProxySelectionPolicy(SelectionPolicy):

    def __init__(self,
                 conn: Client):
        self.conn: Client = conn

    def decision(self,
                 teams: tuple[Team, Team],
                 max_size: int) -> SelectionCommand:
        self.conn.send(('SelectionPolicy', teams, max_size))
        return self.conn.recv()


class ProxyTeamBuildPolicy(TeamBuildPolicy):

    def __init__(self,
                 conn: Client):
        self.conn: Client = conn

    def decision(self,
                 roster: Roster,
                 meta: Meta | None,
                 max_team_size: int,
                 max_pkm_moves: int) -> TeamBuildCommand:
        self.conn.send(('TeamBuildPolicy', roster, meta, max_team_size, max_pkm_moves))
        return self.conn.recv()


class ProxyMetaBalancePolicy(MetaBalancePolicy):

    def __init__(self,
                 conn: Client):
        self.conn: Client = conn

    def decision(self,
                 roster: Roster,
                 meta: Meta,
                 constraints: Constraints) -> RosterBalanceCommand:
        self.conn.send(('BalancePolicy', roster, meta, constraints))
        return self.conn.recv()


class ProxyRuleBalancePolicy(RuleBalancePolicy):

    def __init__(self,
                 conn: Client):
        self.conn: Client = conn

    def decision(self,
                 rules: RuleBalanceCommand) -> RuleBalanceCommand:
        self.conn.send(('RuleBalancePolicy', rules))
        return self.conn.recv()


class ProxyCompetitor(Competitor):

    def __init__(self,
                 conn: Client):
        self.conn = conn
        self._battle_policy = ProxyBattlePolicy(conn)
        self._selection_policy = ProxySelectionPolicy(conn)
        self._team_build_policy = ProxyTeamBuildPolicy(conn)

    @property
    def battle_policy(self) -> BattlePolicy:
        return self._battle_policy

    @property
    def selection_policy(self) -> SelectionPolicy:
        return self._selection_policy

    @property
    def team_build_policy(self) -> TeamBuildPolicy:
        return self._team_build_policy

    @property
    def name(self) -> str:
        self.conn.send(('name',))
        return self.conn.recv()


class ProxyDesignCompetitor(DesignCompetitor):

    def __init__(self,
                 conn: Client):
        self.conn = conn
        self._meta_balance = ProxyMetaBalancePolicy(conn)
        self._rule_balance = ProxyRuleBalancePolicy(conn)

    @property
    def team_predictor(self) -> MetaBalancePolicy:
        return self._meta_balance

    @property
    def balance_policy(self) -> RuleBalancePolicy:
        return self._rule_balance
