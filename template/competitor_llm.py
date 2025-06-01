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

# — Conexión a LM Studio —
def strip_think_tags(text: str) -> str:
    if re.search(r'(?is)<think>.*?</think>', text):
        return re.sub(r'(?is)<think>.*?</think>', '', text).strip()
    else:
        return text

def query_llm(prompt, model_name="deepseek-r1-distill-llama-8b"):
    url = "http://192.168.1.131:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 10000
    }
    logging.info("Enviando prompt a LM Studio (%s):\n%s", model_name, prompt)
    try:
        response = requests.post(url, headers=headers, json=data)
        resp_json = response.json()
        if not response.ok or "choices" not in resp_json:
            logging.error("Respuesta inesperada de %s: %s", model_name, resp_json)
            return []
        content = resp_json["choices"][0]["message"]["content"]
        logging.info("%s respondió (crudo): %s", model_name, content)
        content = strip_think_tags(content)
        logging.info("Contenido limpio: %s", content)
        numbers = re.findall(r'\d+', content)
        result = [int(n) for n in numbers]
        logging.info("Extracción de índices: %s", result)
        return result
    except Exception:
        logging.exception("Error en query_llm:")
        return []

# — Política de team build basada en MCTS+LLM —
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=50):
        self.mcts_iterations = mcts_iterations
        # “last_team” almacenará siempre el último equipo que el LLM devolvió
        self.last_team: list[int] | None = None

    class MCTSState:
        def __init__(self, current_team, roster, log: str = "", max_team_size: int = 3, depth: int = 0):
            self.current_team = current_team
            self.roster = roster
            self.log = log
            self.max_team_size = max_team_size
            self.depth = depth

        def terminal(self) -> bool:
            return self.depth >= 1

        def simulate(self, action):
            return MCTSTeamBuildPolicy.MCTSState(
                action, self.roster, self.log, self.max_team_size, self.depth + 1
            )

    class MCTSNode:
        pass

    def choose_team(self, roster, current_team, log, max_team_size):
        state = MCTSTeamBuildPolicy.MCTSState(current_team, roster, log, max_team_size, depth=0)
        return self.call_llm(state)

    def call_llm(self, state):
        prompt = self.build_prompt(state)
        try:
            indices = query_llm(prompt)
            if not indices or len(indices) != state.max_team_size:
                raise ValueError(f"indices inválidos: {indices}")
            return indices
        except Exception:
            logging.exception("Fallback aleatorio en call_llm:")
            return random.sample(range(len(state.roster)), state.max_team_size)

    def build_prompt(self,
                     roster: list,
                     current_team: list[int],
                     match_outcome: str,
                     new_elo: float | None,
                     winning_indices: list[list[int]]) -> str:
        # 1) Cabecera de resultado anterior
        if "first battle" in match_outcome:
            header = "This is your first battle; no prior result.\n"
        elif "unknown" in match_outcome:
            header = "Your last result could not be determined.\n"
        else:
            header = f"Your last team {match_outcome}."
            if new_elo is not None:
                header += f" Your new Elo is {new_elo:.2f}."
            header += "\n"

        # 2) Lista de índices ganadores de cada partida previa
        if winning_indices:
            wins_str = "; ".join(
                "[" + ", ".join(str(i) for i in win_list) + "]"
                for win_list in winning_indices
            )
            wins_line = f"Winning team indexes in past matches: {wins_str}\n"
        else:
            wins_line = "No past winning-team data available.\n"

        # 3) Roster formateado
        roster_lines = "\n".join(
            f"  {i}: {fmt_pokemon_species(sp)}"
            for i, sp in enumerate(roster)
        )
        prev_team_str = ", ".join(str(i) for i in current_team)

        return (
            header
            + wins_line
            + "Now, given the following:\n"
            + "Roster:\n"
            + roster_lines + "\n"
            + f"Previous team indices: [{prev_team_str}]\n"
            + "Please return exactly the new team indices for example: ---14, 30, 49---"
        )

    def decision(self, roster, meta, max_team_size: int, max_pkm_moves: int, n_active: int):
        """
        1) Recorremos meta.record EN ORDEN cronológico, manteniendo sólo aquellas partidas
           en las que nuestro equipo (self.last_team) coincidía con uno de los dos equipos.
           De cada partida válida extraemos la lista de índices ganadores y la guardamos en
           'winning_indices'.
        2) Determinamos el último match que nos afectó (el más reciente) para sacar match_outcome
           (“won”/“lost”) y new_elo.
        3) Si nunca participamos, asumimos “first battle”.
        """

        # 1) Construir lista de índices ganadores de todas las partidas en las que participamos
        winning_indices: list[list[int]] = []
        last_participation = None  # aquí guardaremos (side, winner, elos) de la última vez que participamos

        # Recorremos meta.record de principio a fin
        for teams, winner, elos in getattr(meta, "record", []):
            ids0 = sorted(p.species.id for p in teams[0].members)
            ids1 = sorted(p.species.id for p in teams[1].members)

            if self.last_team is not None:
                prev = sorted(self.last_team)
            else:
                prev = None

            # Comprobamos si 'prev' coincide con el equipo 0 o el 1
            if prev == ids0:
                # Participamos como “lado 0”
                winning_indices.append(sorted(p.species.id for p in teams[winner].members))
                last_participation = (0, winner, elos)
                # Actualizamos “prev” para la siguiente partida, porque nuestro equipo cambió
                # (self.last_team se actualiza tras cada call_llm)
                # Pero en este loop no lo hacemos, porque aquí sólo reconstruimos historia.

            elif prev == ids1:
                # Participamos como “lado 1”
                winning_indices.append(sorted(p.species.id for p in teams[winner].members))
                last_participation = (1, winner, elos)

            # Si no coincidía con ninguno de los dos, ignoramos esa partida.

        # 2) Determinar resultado de la última participación
        if last_participation is None:
            # Nunca participamos
            match_outcome = "first battle (no prior result)"
            new_elo = None
        else:
            side, winner, elos = last_participation
            match_outcome = "won" if winner == side else "lost"
            new_elo = elos[side]

        # 3) Determinar qué equipo mostrar como “actual”
        if self.last_team is None:
            current_team = list(range(max_team_size))
        else:
            current_team = self.last_team

        logging.info("decision(): last match %s, new Elo %s", match_outcome, new_elo)

        # 4) Construir prompt completo
        prompt = self.build_prompt(roster, current_team, match_outcome, new_elo, winning_indices)
        #logging.info("Sending prompt:\n%s", prompt)
        indices = query_llm(prompt)
        #logging.info("Raw indices: %s", indices)

        # 5) Filtrar índices inválidos y fallback si hace falta
        valid = [i for i in indices if 0 <= i < len(roster)]
        if len(valid) < max_team_size:
            pool = [i for i in range(len(roster)) if i not in valid]
            random.shuffle(pool)
            while len(valid) < max_team_size and pool:
                valid.append(pool.pop())
        elif len(valid) > max_team_size:
            valid = valid[:max_team_size]

        # 6) Guardar el equipo definitivo
        self.last_team = valid

        # 7) Construir el TeamBuildCommand final
        ivs = (31,) * 6
        cmds = []
        for idx in valid:
            sp = roster[idx]
            mv = list(range(len(sp.moves)))[:max_pkm_moves]
            ev = tuple(multinomial(510, [1/6] * 6, size=1)[0])
            nat = Nature(random.randrange(len(Nature)))
            cmds.append((idx, ev, ivs, nat, mv))

        logging.info("Final team indices: %s", valid)
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


if __name__ == "__main__":
    from vgc2.util.generator import gen_move_set, gen_pkm_roster
    move_set = gen_move_set(50)
    roster = gen_pkm_roster(50, move_set)
    max_team_size = 3
    max_pkm_moves = 4
    competitor = LLM_Competitor("MiAgenteLLM_MCTS")
    cmds = competitor.team_build_policy.decision(
        roster, None, max_team_size, max_pkm_moves, n_active=2
    )
    print("Nuevo equipo:", cmds)
