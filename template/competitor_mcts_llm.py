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

##---log---
import logging
import os

# Crear directorio de logs si no exista
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="../logs/competitor.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)
##---fin log---

# — Auxiliares de formateo —
def fmt_pokemon_species(sp):
    hp = sp.base_stats[0]
    types = "/".join(t.name for t in sp.types)
    moves = ", ".join(str(m) for m in sp.moves)
    return f"PkmTemplate(Type={types}, Max_HP={hp}, Moves=[{moves}])"

def fmt_pokemon(p):
    types = "/".join(t.name for t in p.constants.species.types)
    hp = p.hp
    moves = ", ".join(str(m) for m in p.battling_moves)
    return f"Pkm(Type={types}, HP={hp}, Moves=[{moves}])"

# — Conexión a LM Studio —
def query_llm(prompt):
    url = "http://172.26.176.1:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "meta-llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 10000
    }
    logging.info("Enviando prompt a LM Studio:\n%s", prompt)
    response = requests.post(url, headers=headers, data=json.dumps(data))
    content = response.json()["choices"][0]["message"]["content"]
    logging.info("LM Studio respondió: %s", content)
    try:
        numbers = re.findall(r'\d+', content)
        result = [int(n) for n in numbers]
        logging.info("Extracción de índices: %s", result)
        return result
    except Exception as e:
        logging.error("Error al extraer números de LM Studio: %s", e)
        return []  # En caso de error, lista vacía

# — Política de team build basada en MCTS+LLM —
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=50):
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
            # Terminal si depth >= 1
            return self.depth >= 1

        def get_possible_actions(self):
            # Placeholder: no se utiliza porque confiamos en los índices de la IA
            return []

        def simulate(self, action):
            # No usado en el bypass
            return MCTSTeamBuildPolicy.MCTSState(
                action, self.roster, self.log, self.max_team_size, self.depth + 1
            )

    # Nodo de MCTS (no usado en este bypass)
    class MCTSNode:
        pass

    def choose_team(self, roster, current_team, log, max_team_size):
        """
        estado inicial y llamamos directamente al LLM para que proponga indices
        """
        state = MCTSTeamBuildPolicy.MCTSState(current_team, roster, log, max_team_size, depth=0)
        indices = self.call_llm(state)
        return indices

    def call_llm(self, state):
        prompt = self.build_prompt(state)
        indices = query_llm(prompt)
        if not indices:
            # aleatorio si falla y va al mcts
            return random.sample(range(len(state.roster)), state.max_team_size)
        return indices

    def build_prompt(self, state):
        # Formateamos el roster completo
        roster_str = "\n".join(
            f"{idx}: {fmt_pokemon_species(sp)}"
            for idx, sp in enumerate(state.roster)
        )
        team_str = ", ".join(str(i) for i in state.current_team)
        return (
            "Remember to JUST RETURN THE LIST OF THREE INDEXES. DO NOT WRITE ANYTHING ELSE.\n"
            f"Roster:\n{roster_str}\n"
            f"Current Team Indices: [{team_str}]\n"
            f"Log:\n{state.log}\n"
        )

    # Implementación del método abstracto decision
    def decision(self,
                 roster,
                 meta,
                 max_team_size: int,
                 max_pkm_moves: int,
                 n_active: int):
        # Extraer o inicializar valores
        if isinstance(meta, dict):
            current_team = meta.get("current_team", list(range(max_team_size)))
            log_msg = meta.get("log", "")
        else:
            current_team = list(range(max_team_size))
            log_msg = ""
        logging.info("Inicio de decision. Team actual (índices): %s — Log: %s", current_team, log_msg)

        # Obtenemos los índices directamente del LLM
        indices = self.choose_team(roster, current_team, log_msg, max_team_size)
        logging.info("Índices elegidos por LLM: %s", indices)

        # --- NUEVO: mostrar nombres de los Pokémon seleccionados formateados ---
        chosen_fmt = [fmt_pokemon_species(roster[i]) for i in indices]
        logging.info("Pokémon seleccionados: %s", chosen_fmt)

        # Construcción del TeamBuildCommand
        ivs = (31,) * 6
        cmds = []
        for idx in indices:
            sp = roster[idx]
            mv = list(range(len(sp.moves)))[:max_pkm_moves]
            ev = tuple(multinomial(510, [1/6]*6, size=1)[0])
            nat = Nature(random.randrange(len(Nature)))
            cmds.append((idx, ev, ivs, nat, mv))
            logging.debug("Comando para idx %d: %s", idx, cmds[-1])

        # --- NUEVO: log del equipo final por especie/formato ---
        final_fmt = [fmt_pokemon_species(roster[idx]) for idx, *_ in cmds]
        logging.info("Equipo FINAL (por especie): %s", final_fmt)

        logging.info("TeamBuildCommand final: %s", cmds)
        return cmds


class LLM_MCTSCompetitor(Competitor):
    def __init__(self, name: str = "LLM_MCTSCompetitor"):
        self.__name = name
        self.__battle_policy: BattlePolicy = RandomBattlePolicy()
        self.__selection_policy: SelectionPolicy = RandomSelectionPolicy()
        self.__team_build_policy: TeamBuildPolicy = MCTSTeamBuildPolicy(mcts_iterations=50)

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
if __name__ == "__main__":
    from vgc2.util.generator import gen_move_set, gen_pkm_roster
    move_set = gen_move_set(100)
    roster = gen_pkm_roster(50, move_set)
    # Ahora current_team debe pasarse como lista de índices, por ejemplo:
    meta = {"current_team": [0, 1, 2], "log": "Registro de prueba"}
    max_team_size = 3
    max_pkm_moves = 4
    competitor = LLM_MCTSCompetitor("MiAgenteLLM_MCTS")
    decision_command = competitor.team_build_policy.decision(
        roster, meta, max_team_size, max_pkm_moves, n_active=2
    )
    print("Nuevo equipo seleccionado (comando):", decision_command)
