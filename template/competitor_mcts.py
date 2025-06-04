import math
import random
import logging
import os
from itertools import combinations

from numpy.random import multinomial
from vgc2.battle_engine.modifiers import Nature
from vgc2.competition import Competitor
from vgc2.agent import BattlePolicy, SelectionPolicy, TeamBuildPolicy
from vgc2.agent.battle import RandomBattlePolicy
from vgc2.agent.selection import RandomSelectionPolicy

# — Config de logging —
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="../logs/competitorMCTS.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# — Política de team build basada en MCTS mejorado —
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=100):
        self.mcts_iterations = mcts_iterations

    class MCTSState:
        def __init__(self, roster, max_team_size):
            self.roster = roster
            self.max_team_size = max_team_size

        def get_possible_actions(self):
            # Todas las combinaciones posibles de índices de tamaño max_team_size
            return list(combinations(range(len(self.roster)), self.max_team_size))

    class MCTSNode:
        def __init__(self, move=None, parent=None):
            self.move = move            # Tupla de índices
            self.parent = parent
            self.children = []
            self.visits = 0
            self.wins = 0

        def uct_score(self, total_simulations, c=1.414):
            if self.visits == 0:
                return float('inf')
            exploitation = self.wins / self.visits
            exploration = c * math.sqrt(math.log(total_simulations) / self.visits)
            return exploitation + exploration

    def choose_team(self, roster, current_team, log, max_team_size):
        # nodo raiz
        root = self.MCTSNode()

        # acciones posibles y expandimos hijos
        actions = self.MCTSState(roster, max_team_size).get_possible_actions()
        for act in actions:
            root.children.append(self.MCTSNode(move=act, parent=root))

        # si no hay hijos validos aleatorio
        if not root.children:
            # Seleccionamos max_team_size ind distintos de manera aleatoria
            return random.sample(range(len(roster)), max_team_size)

        # el MCTS
        for _ in range(self.mcts_iterations):
            # Seleccion y desempate aleatorio 
            total_visits = root.visits + 1  # para evitar division entre cero edel UCT
            uct_values = [child.uct_score(total_visits) for child in root.children]
            best_score = max(uct_values)

            # recolectamos todos los indices que empatan
            best_indices = [i for i, v in enumerate(uct_values) if abs(v - best_score) < 1e-9]

            # Si best_indices queda vacio, aleatorio
            if not best_indices:
                node = random.choice(root.children)
            else:
                chosen_index = random.choice(best_indices)
                node = root.children[chosen_index]

            # Simulacion con desempate aleatorio
            reward = self.simulate_rollout(node.move, roster, max_team_size)

            # Backpropagation
            node.visits += 1
            node.wins += reward
            root.visits += 1

        # elegimos hijo con mayor ratio wins/visits
        best_child = max(
            root.children,
            key=lambda n: (n.wins / n.visits) if n.visits > 0 else 0
        )
        return list(best_child.move)

    def simulate_rollout(self, team_indices, roster, max_team_size):
        # Construimos equipo rival aleatorio
        all_indices = set(range(len(roster)))
        pool = list(all_indices - set(team_indices))
        if len(pool) < max_team_size:
            opponent = random.sample(range(len(roster)), max_team_size)
        else:
            opponent = random.sample(pool, max_team_size)

        # Calculamos resultado sumando todas las estats base
        def team_score(indices):
            return sum(sum(roster[i].base_stats) for i in indices)

        score_A = team_score(team_indices)
        score_B = team_score(opponent)

        # vemos quien gana o si es empate pues random
        if score_A > score_B:
            return 1
        elif score_A < score_B:
            return 0
        else:
            return random.choice([0, 1])

    def decision(self, roster, meta, max_team_size: int, max_pkm_moves: int, n_active: int):
        logging.info("Iniciando MCTS con %d iteraciones", self.mcts_iterations)

        # indices del equipo mediante MCTS
        indices = self.choose_team(roster, None, "", max_team_size)
        logging.info("Indices elegidos por MCTS: %s", indices)

        # el TeamBuildCommand
        ivs = (31,) * 6
        cmds = []
        for idx in indices:
            sp = roster[idx]
            mv = list(range(len(sp.moves)))[:max_pkm_moves]
            ev = tuple(multinomial(510, [1/6]*6, size=1)[0])
            nat = Nature(random.randrange(len(Nature)))
            cmds.append((idx, ev, ivs, nat, mv))
            logging.debug("Comando generado para idx %d: %s", idx, cmds[-1])

        logging.info("TeamBuildCommand final: %s", cmds)
        return cmds


class MCTSCompetitor(Competitor):
    def __init__(self, name: str = "MCTSCompetitor"):
        self.__name = name
        self.__battle_policy = RandomBattlePolicy()
        self.__selection_policy = RandomSelectionPolicy()
        self.__team_build_policy = MCTSTeamBuildPolicy(mcts_iterations=100)

    @property
    def battle_policy(self) -> BattlePolicy | None:
        return self.__battle_policy

    @property
    def selection_policy(self) -> SelectionPolicy | None:
        return self.__selection_policy

    @property
    def team_build_policy(self) -> TeamBuildPolicy | None:
        return self.__team_build_policy

    @property
    def name(self) -> str:
        return self.__name


# — Bloque de prueba —
if __name__ == "__main__":
    from vgc2.util.generator import gen_move_set, gen_pkm_roster
    move_set = gen_move_set(100)
    roster = gen_pkm_roster(50, move_set)
    max_team_size = 3
    max_pkm_moves = 4

    competitor = MCTSCompetitor("AgenteMCTS")
    cmds = competitor.team_build_policy.decision(
        roster, None, max_team_size, max_pkm_moves, n_active= max_team_size
    )
    print("Nuevo equipo seleccionado (comando):", cmds)
