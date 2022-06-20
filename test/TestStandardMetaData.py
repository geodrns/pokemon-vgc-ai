import unittest

from vgc.balance.meta import StandardMetaData
from vgc.datatypes.Objects import PkmFullTeam
from vgc.util.generator.PkmRosterGenerators import RandomPkmRosterGenerator


class TestStandardMetaData(unittest.TestCase):
    roster = None
    move_roster = None

    @classmethod
    def setUpClass(cls):
        generator = RandomPkmRosterGenerator()
        cls.roster = generator.gen_roster()
        cls.move_roster = generator.base_move_roster

    def setUp(self):
        self.meta_data = StandardMetaData()
        self.meta_data.set_moves_and_pkm(self.roster, self.move_roster)

    def test_init(self):
        self.assertEqual(self.meta_data.get_n_teams(), 0)
        self.assertEqual(len(self.meta_data._pkm_usage), len(self.roster))
        self.assertEqual(len(self.meta_data._pkm_wins), len(self.roster))
        self.assertEqual(len(self.meta_data._move_usage), len(self.move_roster))
        self.assertEqual(len(self.meta_data._move_wins), len(self.move_roster))
        self.assertEqual(len(self.meta_data._moves), len(self.move_roster))
        self.assertEqual(len(self.meta_data._pkm), len(self.roster))
        self.assertEqual(len(self.meta_data._d_move), len(self.move_roster) ** 2)
        self.assertEqual(len(self.meta_data._d_pkm), len(self.roster) ** 2)

    def test_update_with_team(self):
        templates = list(self.roster)
        pkms = [templates[i].gen_pkm([0, 1, 2, 3]) for i in range(4)]
        full_team = PkmFullTeam(pkms[0:3])
        self.meta_data.update_with_team(full_team, True)
        self.assertEqual(self.meta_data.get_n_teams(), 1)
        self.assertEqual(self.meta_data.get_global_pkm_usage(pkms[0].pkm_id), 1 / 3)
        self.assertEqual(self.meta_data.get_global_pkm_winrate(pkms[0].pkm_id), 1)
        self.assertEqual(self.meta_data.get_pair_usage((pkms[0].pkm_id, pkms[1].pkm_id)), 1)
        self.assertEqual(self.meta_data.get_pair_usage((pkms[0].pkm_id, pkms[3].pkm_id)), 0)
        full_team_2 = PkmFullTeam(pkms[1:4])
        self.meta_data.update_with_team(full_team_2, True)
        self.assertEqual(self.meta_data.get_n_teams(), 2)
        self.assertEqual(self.meta_data.get_global_pkm_usage(pkms[0].pkm_id), 1 / 6)
        self.assertEqual(self.meta_data.get_global_pkm_winrate(pkms[0].pkm_id), 1)
        self.assertEqual(self.meta_data.get_pair_usage((pkms[0].pkm_id, pkms[1].pkm_id)), 1 / 2)
        self.assertEqual(self.meta_data.get_pair_usage((pkms[1].pkm_id, pkms[2].pkm_id)), 1)
