import math
import random
import json
import requests
import re

from numpy.random import multinomial
from vgc2.battle_engine.modifiers import Nature
from vgc2.competition import Competitor
from vgc2.agent import BattlePolicy, SelectionPolicy, TeamBuildPolicy
from vgc2.agent.battle import RandomBattlePolicy
from vgc2.agent.selection import RandomSelectionPolicy

# Función para conectar con LM Studio (adaptada para extraer una lista de dígitos)
def query_llm(prompt):
    url = "http://192.168.1.136:1234/v1/chat/completions"  # API de LM Studio 192.168.1.136    ext: 10.163.144.61
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "deepseek-r1-distill-llama-8b",  # deepseek-r1-distill-llama-8b  meta-llama-3.1-8b-instruct
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 10000
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    content = response.json()["choices"][0]["message"]["content"]
    try:
        # Se buscan todos los números en el contenido y se convierten en enteros
        numbers = re.findall(r'\d+', content)
        return [int(n) for n in numbers]
    except Exception:
        return []  # En caso de error, se retorna una lista vacía

# Política de team build basada en MCTS con integración de LM Studio
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=100):
        self.mcts_iterations = mcts_iterations

    # Estado simplificado para team building
    class MCTSState:
        def __init__(self, current_team, roster, log: str = "", max_team_size: int = 3, depth: int = 0):
            self.current_team = current_team
            self.roster = roster
            self.log = log
            self.max_team_size = max_team_size
            self.depth = depth

        def terminal(self) -> bool:
            # En este ejemplo consideramos terminal si ya se ha tomado la decisión (depth >= 1)
            return self.depth >= 1

        def get_possible_actions(self):
            # Genera acciones de ejemplo: combinaciones de índices para formar un equipo.
            # En una implementación real se generarían las combinaciones legales a partir del roster.
            return [
                [0, 1, 2],
                [0, 2, 3],
                [1, 2, 3],
                [0, 1, 3]
            ]

        def simulate(self, action):
            # Simula aplicar la acción: incrementa depth y fija el equipo a la acción propuesta
            return MCTSTeamBuildPolicy.MCTSState(action, self.roster, self.log, self.max_team_size, self.depth + 1)

    # Nodo del árbol de búsqueda MCTS
    class MCTSNode:
        def __init__(self, game_state, parent=None, move=None):
            self.game_state = game_state
            self.parent = parent
            self.move = move
            self.children = []
            self.visits = 0
            self.wins = 0

        def is_terminal(self):
            return self.game_state.terminal()

        def is_fully_expanded(self):
            return len(self.children) == len(self.game_state.get_possible_actions())

        def best_uct_child(self, exploration_param=1.414):
            best_value = -float('inf')
            best_child = None
            for child in self.children:
                if child.visits == 0:
                    uct_value = float('inf')
                else:
                    exploitation = child.wins / child.visits
                    exploration = exploration_param * math.sqrt(math.log(self.visits) / child.visits)
                    uct_value = exploitation + exploration
                if uct_value > best_value:
                    best_value = uct_value
                    best_child = child
            return best_child

        def expand(self):
            tried_moves = [child.move for child in self.children]
            for move in self.game_state.get_possible_actions():
                if move not in tried_moves:
                    new_state = self.game_state.simulate(move)
                    new_node = MCTSTeamBuildPolicy.MCTSNode(new_state, parent=self, move=move)
                    self.children.append(new_node)
                    return new_node
            return None

    # Ejecuta la búsqueda MCTS para escoger el equipo óptimo
    def choose_team(self, roster, current_team, log, max_team_size):
        initial_state = MCTSTeamBuildPolicy.MCTSState(current_team, roster, log, max_team_size, depth=0)
        root = MCTSTeamBuildPolicy.MCTSNode(initial_state)

        for _ in range(self.mcts_iterations):
            node = self.selection(root)
            reward = self.simulation(node.game_state)
            self.backpropagation(node, reward)

        best_child = max(root.children, key=lambda c: c.wins / c.visits if c.visits > 0 else 0)
        return best_child.move

    def selection(self, node):
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node.expand()
            else:
                node = node.best_uct_child()
        return node

    def simulation(self, game_state):
        action = self.call_llm(game_state)
        simulated_state = game_state.simulate(action)
        return self.evaluate_state(simulated_state)

    def backpropagation(self, node, reward: float):
        while node is not None:
            node.visits += 1
            node.wins += reward
            node = node.parent

    # llamada a LM Studio: se construye el prompt y se llama a query_llm
    def call_llm(self, game_state):
        prompt = self.build_prompt(game_state)
        indices = query_llm(prompt)
        if not indices:
            # si LM Studio no responde correctamente, se hace una aleatoria
            possible_actions = game_state.get_possible_actions()
            return random.choice(possible_actions)
        return indices

    def build_prompt(self, game_state):
        # prompt en ingles bc mas facil para deepseek
        prompt = (
            "You are a team building machine of a simplified version of pokemon. You will receive a Roster, a Team and a Veredict in a dictionary format. The Roster will be a list with the only possibilities to form a new team to win the next battle competition. The Team will be the last team used in the battle competition. And the Veredict will be a number that represents the number of victories in the last battle competition, the higher this number is the better. With this data you will have to make a new team from the Roster that will win the next battle competiton. Return the results in a list with the three indexes of the chosen pokemon from the Roster. JUST RETURN THE LIST OF THREE INDEXES. DO NOT WRITE ANYTHING ELSE. Return the response according with the following format inside the --- pattern: ---index1, index2, index3---, for example: ---14, 30, 50---. The response must be only simple text, no markdown. No explanation is needed. The teams must be of three pokemon, so just return 3 indexes in the specified format.\n"
            f"Roster: {game_state.roster}\n"
            f"Equipo actual: {game_state.current_team}\n"
            f"Log: {game_state.log}\n"
            )
        return prompt

    def evaluate_state(self, game_state):
        if game_state.terminal():
            return 1
        return 0.5

    # Implementación del método abstracto decision
    def decision(self,
                 roster,
                 meta,
                 max_team_size: int,
                 max_pkm_moves: int,
                 n_active: int):
        # Extraer información de meta o usar valores por defecto
        if meta is not None and isinstance(meta, dict):
            current_team = meta.get("current_team", roster[:max_team_size])
            log = meta.get("log", "")
        else:
            current_team = roster[:max_team_size]
            log = ""
        # Obtener los índices seleccionados por el algoritmo MCTS (por ejemplo, [0, 1, 2])
        indices = self.choose_team(roster, current_team, log, max_team_size)
        
        # Transformar los índices en un comando válido para construir el equipo.
        ivs = (31, 31, 31, 31, 31, 31)
        cmds = []
        for index in indices:
            pokemon = roster[index]
            n_moves = len(pokemon.moves)
            # Selecciona aleatoriamente hasta max_pkm_moves movimientos
            moves = list(random.sample(range(n_moves), min(max_pkm_moves, n_moves))) if n_moves > 0 else []
            evs = tuple(multinomial(510, [1/6]*6, size=1)[0])
            nature = Nature(random.choice(range(len(Nature))))
            cmds.append((index, evs, ivs, nature, moves))
        return cmds

# Competidor que utiliza la política MCTS en team build, manteniendo las otras políticas aleatorias
class MCTSCompetitor(Competitor):
    def __init__(self, name: str = "MCTSCompetitor"):
        self.__name = name
        self.__battle_policy: BattlePolicy = RandomBattlePolicy()
        self.__selection_policy: SelectionPolicy = RandomSelectionPolicy()
        self.__team_build_policy: TeamBuildPolicy = MCTSTeamBuildPolicy(mcts_iterations=100)

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

# Bloque de prueba para verificar la política de team build
from vgc2.util.generator import gen_move_set, gen_pkm_roster

if __name__ == "__main__":
    move_set = gen_move_set(100)
    roster = gen_pkm_roster(50, move_set)
    # Para el test, también puedes obtener un equipo inicial de ejemplo (no se usan aquí directamente)
    current_team = roster[:3]  # O algún equipo válido según la estructura
    meta = {"current_team": current_team, "log": "Registro de las últimas jugadas."}
    max_team_size = 3
    max_pkm_moves = 4
    n_active = 2

    competitor = MCTSCompetitor("MiAgenteMCTS")
    decision_command = competitor.team_build_policy.decision(roster, meta, max_team_size, max_pkm_moves, n_active)
    print("Nuevo equipo seleccionado (comando):", decision_command)

