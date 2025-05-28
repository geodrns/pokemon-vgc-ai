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
    url = "http://192.168.1.131:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "meta-llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 10000
    }
    logging.info("Enviando prompt a LM Studio:\n%s", prompt)
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        resp_json = response.json()
        if not response.ok or "choices" not in resp_json:
            logging.error("Respuesta inesperada de LM Studio: %s", resp_json)
            return []
        content = resp_json["choices"][0]["message"]["content"]
        logging.info("LM Studio respondió: %s", content)
        numbers = re.findall(r'\d+', content)
        result = [int(n) for n in numbers]
        logging.info("Extracción de índices: %s", result)
        return result
    except requests.RequestException as e:
        logging.error("Error HTTP en query_llm: %s", e)
        return []
    except ValueError as e:
        logging.error("No se pudo decodificar JSON de LM Studio: %s", e)
        return []
    except Exception as e:
        logging.exception("Error inesperado en query_llm:")
        return []

# — Política de team build basada en MCTS+LLM —
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=50):
        self.mcts_iterations = mcts_iterations
        # guardará el último equipo que devolvimos (lista de índices)
        self.last_team: list[int] | None = None

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
        try:
            indices = query_llm(prompt)
            if not indices or len(indices) != state.max_team_size:
                raise ValueError(f"indices inválidos: {indices}")
            return indices
        except Exception as e:
            logging.exception("Fallo en call_llm, usando fallback aleatorio:")
            #usamos el aleatorio
            return random.sample(range(len(state.roster)), state.max_team_size)

    def build_prompt(self, roster: list, current_team: list[int], veredict: int) -> str:
        roster_items = [
            f"    {i}: {fmt_pokemon_species(sp)}"
            for i, sp in enumerate(roster)
        ]
        roster_str = ",\n".join(roster_items)
        team_str   = ", ".join(str(i) for i in current_team)
        
        # 4) Montamos el prompt en forma de diccionario literal
        prompt = (
            f"  \"Roster\": [\n{roster_str}\n  ],\n"
            f"  \"Team\": [{team_str}],\n"
            f"  \"Veredict\": {veredict}\n"
            "}\n"
        )
        return prompt


    # Implementación del método abstracto decision
    def decision(self,
                 roster,
                 meta,
                 max_team_size: int,
                 max_pkm_moves: int,
                 n_active: int):
        # 1) Determinamos qué equipo le pasamos al LLM:
        if self.last_team is None:
            # si es la PRIMERA ronda, ponemos el default
            current_team = list(range(max_team_size))
            veredict     = 0
        else:
            current_team = self.last_team
            # aquí podrías calcular un veredict real (p.ej. #victorias)
            veredict     = 1  

        logging.info("Inicio de decision. Team actual (índices): %s", current_team)

        # 2) Construimos y enviamos el prompt
        prompt = self.build_prompt(roster, current_team, veredict)
        logging.info("Enviando prompt a LM Studio:\n%s", prompt)
        indices = query_llm(prompt)
        if not indices:
            # fallback aleatorio
            indices = random.sample(range(len(roster)), max_team_size)
        logging.info("Índices elegidos por LLM: %s", indices)

        # 3) Ya tenemos el nuevo equipo: ¡lo guardamos para la próxima ronda!
        self.last_team = indices

        # 4) Construimos el TeamBuildCommand
        ivs = (31,) * 6
        cmds = []
        for idx in indices:
            sp = roster[idx]
            mv = list(range(len(sp.moves)))[:max_pkm_moves]
            ev = tuple(multinomial(510, [1/6]*6, size=1)[0])
            nat = Nature(random.randrange(len(Nature)))
            cmds.append((idx, ev, ivs, nat, mv))
            logging.debug("Comando para idx %d: %s", idx, cmds[-1])

        # 5) Log final
        final_fmt = [fmt_pokemon_species(roster[i]) for i in indices]
        logging.info("Equipo FINAL (por especie): %s", final_fmt)
        logging.info("TeamBuildCommand final: %s", cmds)

        return cmds


class LLM_Competitor(Competitor):
    def __init__(self, name: str = "LLM_Competitor"):
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
    competitor = LLM_Competitor("MiAgenteLLM_MCTS")
    decision_command = competitor.team_build_policy.decision(
        roster, meta, max_team_size, max_pkm_moves, n_active=2
    )
    print("Nuevo equipo seleccionado (comando):", decision_command)
