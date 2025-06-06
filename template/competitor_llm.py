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

# — Aux de formateo —
def fmt_pokemon_species(sp):
    hp = sp.base_stats[0]
    types = "/".join(t.name for t in sp.types)
    moves = ", ".join(str(m) for m in sp.moves)
    return f"PkmTemplate(Type={types}, Max_HP={hp}, Moves=[{moves}])"

# — Conexion a LM Studio —
def strip_think_tags(text: str) -> str:
    if re.search(r'(?is)<think>.*?</think>', text):
        return re.sub(r'(?is)<think>.*?</think>', '', text).strip()
    else:
        return text

def query_llm(prompt, model_name="deepseek-r1-distill-llama-8b"): # meta-llama-3.1-8b-instruct
    url = "http://192.168.1.131:1234/v1/chat/completions" #ajustar dependiendo del puerto
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 8000
    }
    logging.info("Enviando prompt a LM Studio (%s):\n%s", model_name, prompt)
    try:
        response = requests.post(url, headers=headers, json=data, timeout=400)
        resp_json = response.json()
        if not response.ok or "choices" not in resp_json:
            logging.error("Respuesta inesperada de %s: %s", model_name, resp_json)
            return []
        content = resp_json["choices"][0]["message"]["content"]
        logging.info("%s respondio: %s", model_name, content)
        content = strip_think_tags(content) # para deepseek
        logging.info("Contenido limpio: %s", content) # cuando se proporcionan indices de más
        numbers = re.findall(r'\d+', content) # aqui se dedica a encontrar todos los numeros
        result = [int(n) for n in numbers]
        logging.info("Extracción de índices: %s", result)# despues de los filtros deben ser 3
        return result
    except Exception:
        logging.exception("Error en query_llm:")
        return []

# — Politica de team build basada en MCTS+LLM —
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=50):
        self.mcts_iterations = mcts_iterations
        # “last_team” almacenará siempre el último equipo que el LLM devolvió
        self.last_team: list[int] | None = None
        # Aquí guardamos todos los equipos ganadores a lo largo de la competición
        self.winning_teams_history: list[list[int]] = []
        # Aquí guardamos todos los equipos perdedores a lo largo de la competición
        self.losing_teams_history: list[list[int]] = []

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
                     winning_indices: list[list[int]],
                     losing_indices: list[list[int]]) -> str:
        # Cabecera de resultado anterior
        if "first battle" in match_outcome:
            header = "This is your first battle; no prior result.\n"
        elif "unknown" in match_outcome:
            header = "Your last result could not be determined.\n"
        else:
            header = f"Your last team {match_outcome}."
            if new_elo is not None:
                header += f" Your new Elo is {new_elo:.2f}."
            header += "\n"

        # Lista de indices ganadores previos
        if winning_indices:
            wins_lines = "\n".join(
                "[" + ", ".join(str(i) for i in win_list) + "]"
                for win_list in winning_indices
            )
            wins_line = f"Winning team indexes in past matches:\n{wins_lines}\n"
        else:
            wins_line = "No past winning-team data available\n"

        # Lista de idices perdedores previos
        if losing_indices:
            loses_lines = "\n".join(
                "[" + ", ".join(str(i) for i in lose_list) + "]"
                for lose_list in losing_indices
            )
            loses_line = f"Losing team indexes in past matches:\n{loses_lines}\n"
        else:
            loses_line = "No past losing-team data available\n"

        # roster formateado
        roster_lines = "\n".join(
            f"  {i}: {fmt_pokemon_species(sp)}"
            for i, sp in enumerate(roster)
        )

        # Si es la primera batalla no incluimos los equipos previos ya q no hay
        if "first battle" in match_outcome:
            prev_line = ""
        else:
            prev_team_str = ", ".join(str(i) for i in current_team)
            prev_line = f"Previous team indices: [{prev_team_str}]\n"

        return (
            header
            + wins_line
            + loses_line
            + "Now, given the following:\n"
            + "Roster:\n"
            + roster_lines + "\n"
            + prev_line
            + "Please return exactly the new team indices following this format: ---id1, id2, id3---" #repetimos el formato para asegurarnos q se respondera asi
        )

    def decision(self, roster, meta, max_team_size: int, max_pkm_moves: int, n_active: int):
        #en decision buscaremos la ult partida que el equipo jugo y si ganamos lo añadimos al history de winning teams
        #si perdemos viceversa. Luego se tertermina si se ha ganado o perdido y el nuevo elo
       
        # PRIEMRO: vemos meta.record y self.last_team para ver la ult participacion concreta
        last_participation = None  # aqui guardamos (side, winner, elos, team_ids) de la ult vez que participamos

        # Si tenemos algun registro y ya enviamos el equipo la otr avez
        if getattr(meta, "record", []) and self.last_team is not None:
            # Recorremos meta.record hasta encontrar la primera coincidencia
            for teams, winner, elos in reversed(meta.record):
                ids0 = sorted(p.species.id for p in teams[0].members)
                ids1 = sorted(p.species.id for p in teams[1].members)
                prev_sorted = sorted(self.last_team)
                if prev_sorted == ids0:
                    last_participation = (0, winner, elos, ids0)
                    break
                elif prev_sorted == ids1:
                    last_participation = (1, winner, elos, ids1)
                    break

        # det el resultado de la ult participacion
        if last_participation is None:
            # Nunca participamos por lo q es la first 
            match_outcome = "first battle (no prior result)"
            new_elo = None
        else:
            side, winner, elos, team_ids = last_participation
            match_outcome = "won" if winner == side else "lost"
            new_elo = elos[side]
            # Si ganamos, se añadde a los equipos ganadores
            if winner == side:
                self.winning_teams_history.append(team_ids)
            else:
                # Si perdemos, al otro
                self.losing_teams_history.append(team_ids)

        # determinamos q equipo mostrar como el actual
        if self.last_team is None:
            current_team = list(range(max_team_size))
        else:
            current_team = self.last_team

        logging.info("decision(): last match %s, new Elo %s", match_outcome, new_elo)

        # aqui construimos el prompt al completo
        prompt = self.build_prompt(
            roster,
            current_team,
            match_outcome,
            new_elo,
            self.winning_teams_history,
            self.losing_teams_history
        )
        indices = query_llm(prompt) #enviamos finalmente el prompt al LLM

        # filtramos los indices y si no son validos aplicamos el randomizer
        valid = [i for i in indices if 0 <= i < len(roster)]
        if len(valid) < max_team_size:
            pool = [i for i in range(len(roster)) if i not in valid]
            random.shuffle(pool)
            while len(valid) < max_team_size and pool:
                valid.append(pool.pop())
        elif len(valid) > max_team_size:
            valid = valid[:max_team_size]

        # finalmente el equipo
        self.last_team = valid

        # el TeamBuildCommand final:
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
