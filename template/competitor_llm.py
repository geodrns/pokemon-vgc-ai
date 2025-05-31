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
def strip_think_tags(text: str) -> str:
    if re.search(r'(?is)<think>.*?</think>', text):
        return re.sub(r'(?is)<think>.*?</think>', '', text).strip()
    else:
        return text

def query_llm(prompt, model_name="meta-llama-3.1-8b-instruct"):
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
    except Exception as e:
        logging.exception("Error en query_llm:")
        return []

# — Política de team build basada en MCTS+LLM —
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=50):
        self.mcts_iterations = mcts_iterations
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

    def build_prompt(self, roster: list, current_team: list[int],
                     match_outcome: str, new_elo: float | None) -> str:
        # Cabecera
        if "first battle" in match_outcome:
            header = "This is your first battle; no prior result.\n"
        elif "unknown" in match_outcome:
            header = "Your last result could not be determined.\n"
        else:
            header = f"Your last team {match_outcome}."
            if new_elo is not None:
                header += f" Your new Elo is {new_elo:.2f}."
            header += "\n"

        roster_lines = "\n".join(
            f"  {i}: {fmt_pokemon_species(sp)}"
            for i, sp in enumerate(roster)
        )
        prev_team_str = ", ".join(str(i) for i in current_team)

        return (
            header
            + "Now, given the following:\n"
            + "Roster:\n"
            + roster_lines + "\n"
            + f"Previous team indices: [{prev_team_str}]\n"
            + "Please return exactly the new team indices for example: ---14, 30, 50---"
        )

    def decision(self, roster, meta, max_team_size: int, max_pkm_moves: int, n_active: int):
        # 1) Último registro de partido
        if getattr(meta, "record", []):
            teams, winner, elos = meta.record[-1]
            ids0 = sorted(p.species.id for p in teams[0].members)
            ids1 = sorted(p.species.id for p in teams[1].members)
            prev = sorted(self.last_team) if self.last_team is not None else None
            if prev == ids0:
                side = 0
            elif prev == ids1:
                side = 1
            else:
                side = None
            if side is None:
                match_outcome = "result unknown"
                new_elo = None
            else:
                match_outcome = "won" if winner == side else "lost"
                new_elo = elos[side]
        else:
            match_outcome = "first battle (no prior result)"
            new_elo = None

        # 2) Equipo previo
        if self.last_team is None:
            current_team = list(range(max_team_size))
        else:
            current_team = self.last_team

        logging.info("decision(): last match %s, new Elo %s", match_outcome, new_elo)

        # 3) Prompt y llamada LLM
        prompt = self.build_prompt(roster, current_team, match_outcome, new_elo)
        logging.info("Sending prompt:\n%s", prompt)
        indices = query_llm(prompt)
        logging.info("Raw indices: %s", indices)

        # 4) Limpieza
        valid = [i for i in indices if 0 <= i < len(roster)]
        if len(valid) < max_team_size:
            pool = [i for i in range(len(roster)) if i not in valid]
            random.shuffle(pool)
            while len(valid) < max_team_size and pool:
                valid.append(pool.pop())
        elif len(valid) > max_team_size:
            valid = valid[:max_team_size]

        self.last_team = valid

        # 5) Construcción de comandos
        ivs = (31,) * 6
        cmds = []
        for idx in valid:
            sp = roster[idx]
            mv = list(range(len(sp.moves)))[:max_pkm_moves]
            ev = tuple(multinomial(510, [1/6]*6, size=1)[0])
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
    move_set = gen_move_set(100)
    roster = gen_pkm_roster(50, move_set)
    max_team_size = 3
    max_pkm_moves = 4
    competitor = LLM_Competitor("MiAgenteLLM_MCTS")
    cmds = competitor.team_build_policy.decision(
        roster, None, max_team_size, max_pkm_moves, n_active=2
    )
    print("Nuevo equipo:", cmds)
