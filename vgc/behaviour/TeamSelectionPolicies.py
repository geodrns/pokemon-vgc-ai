import random
from typing import Set, Tuple

import PySimpleGUI as sg

from vgc.behaviour import TeamSelectionPolicy
from vgc.datatypes.Constants import DEFAULT_TEAM_SIZE, MAX_TEAM_SIZE
from vgc.datatypes.Objects import PkmFullTeam


class RandomTeamSelectionPolicy(TeamSelectionPolicy):

    def __init__(self, teams_size: int = DEFAULT_TEAM_SIZE, selection_size: int = DEFAULT_TEAM_SIZE):
        self.teams_size = teams_size
        self.selection_size = selection_size

    def get_action(self, d: Tuple[PkmFullTeam, PkmFullTeam]) -> Set[int]:
        """

        :param d: (self, opponent)
        :return: idx list of selected pokémon
        """
        ids = [i for i in range(self.teams_size)]
        random.shuffle(ids)
        return set(ids[:self.selection_size])


class FirstEditionTeamSelectionPolicy(TeamSelectionPolicy):

    def get_action(self, d: Tuple[PkmFullTeam, PkmFullTeam]) -> Set[int]:
        """
        Teams are selected as they are.

        :param d: (self, opponent)
        :return: idx list of selected pokémon
        """
        return {0, 1, 2}


class TerminalTeamSelection(TeamSelectionPolicy):

    def get_action(self, s: Tuple[PkmFullTeam, PkmFullTeam]) -> Set[int]:
        print('~ Opponent Team ~')
        for p in s[0].pkm_list:
            print(p)
        for i, p in enumerate(s[0].pkm_list):
            print(i, '->', p)
        print('Select action in the format p p p with p in [0-5]')
        while True:
            valid = True
            try:
                t = input('Select Action: ')
                t = t.split()
                if len(t) != 3:
                    print('Invalid action. Select again.')
                    continue
                for m in t:
                    if not m.isdigit() and 0 < int(m) < len(s[0].pkm_list):
                        print('Invalid action. Select again.')
                        valid = False
                        break
                if valid:
                    break
            except:
                print('Invalid action. Select again.')
        print()
        return {int(t[0]), int(t[1]), int(t[2])}


class GUITeamSelectionPolicy(TeamSelectionPolicy):

    def __init__(self, selected_team_size: int = DEFAULT_TEAM_SIZE, full_team_size: int = MAX_TEAM_SIZE):
        self.selected_team_size = selected_team_size
        self.opp_title = sg.Text('Opponent Team:')
        self.opp = [[sg.Text('                                      ')] for _ in range(full_team_size)]
        self.team_title = sg.Text('Your Team:')
        self.team = [
            [sg.Text('                                      '),
             sg.Checkbox('Pkm ' + str(i), size=(10, 1), default=False, enable_events=True)] for i in
            range(full_team_size)]
        self.select = sg.ReadFormButton('Select', bind_return_key=True)
        layout = [[self.opp_title]] + self.opp + [[self.team_title]] + self.team + [[self.select]]
        self.window = sg.Window('Pokemon Battle Engine', layout)
        self.window.Finalize()
        self.select.Update(disabled=True)

    def get_action(self, d: Tuple[PkmFullTeam, PkmFullTeam]) -> Set[int]:

        """:param d: (self, opponent)
        :return: idx list of selected pokémon"""

        selected = []
        for item in self.team:
            item[1].Update(value=False)
        # opponent party
        opp_team = d[1]
        for i in range(len(opp_team)):
            pkm = opp_team.pkm_list[i]
            self.opp[i][0].Update(pkm.type.name + ' ' + str(pkm.hp) + ' HP')
        # my party
        my_team = d[0]
        for i in range(len(my_team)):
            pkm = my_team.pkm_list[i]
            self.team[i][0].Update(pkm.type.name + ' ' + str(pkm.hp) + ' HP')
        event, values = self.window.read()
        while event != self.select.get_text():
            if event not in selected:
                selected.append(event)
            else:
                selected.remove(event)
            self.select.Update(disabled=self.selected_team_size != len(selected))
            event, values = self.window.read()
        return set(selected)

    def close(self):
        self.window.close()
