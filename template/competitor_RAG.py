import math
import random
import json
import requests
import re
import os
import logging

from numpy.random import multinomial
from vgc2.battle_engine.modifiers import Nature
from vgc2.competition import Competitor
from vgc2.agent import BattlePolicy, SelectionPolicy, TeamBuildPolicy
from vgc2.agent.battle import RandomBattlePolicy
from vgc2.agent.selection import RandomSelectionPolicy

# — Helpers for formatting —
def fmt_pokemon_species(sp):
    hp    = sp.base_stats[0]
    types = "/".join(t.name for t in sp.types)
    moves = ", ".join(str(m) for m in sp.moves)
    return f"PkmTemplate(Type={types}, Max_HP={hp}, Moves=[{moves}])"

# — LM Studio query —
def query_llm(prompt):
    url     = "http://192.168.1.131:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data    = {
        "model":      "meta-llama-3.1-8b-instruct",
        "messages":   [{"role":"user","content":prompt}],
        "temperature":0.7,
        "max_tokens":10000
    }
    logging.info("Enviando prompt a LM Studio:\n%s", prompt)
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        resp = response.json()
        if not response.ok or "choices" not in resp:
            logging.error("Respuesta inesperada de LM Studio: %s", resp)
            return []
        content = resp["choices"][0]["message"]["content"]
        logging.info("LM Studio respondió: %s", content)
        nums = re.findall(r'\d+', content)
        result = [int(n) for n in nums]
        logging.info("Extracción de índices: %s", result)
        return result
    except Exception as e:
        logging.exception("Error en query_llm:")
        return []

# — Logging setup (overwrite each run) —
os.makedirs("..//logs", exist_ok=True)
logging.basicConfig(
    filename="../logs/RAG.log",
    filemode='w',
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# — MCTS+LLM TeamBuildPolicy that also dumps RAG.txt —
class MCTSTeamBuildPolicy(TeamBuildPolicy):
    def __init__(self, mcts_iterations=50):
        self.mcts_iterations = mcts_iterations
        self.last_team = None  # will hold last chosen indices

    class MCTSState:
        def __init__(self, current_team, roster, log:str, max_team_size:int, depth:int):
            self.current_team = current_team
            self.roster       = roster
            self.log          = log
            self.max_team_size= max_team_size
            self.depth        = depth
        def terminal(self): return self.depth >= 1
        def get_possible_actions(self): return []
        def simulate(self,action): return MCTSTeamBuildPolicy.MCTSState(action,self.roster,self.log,self.max_team_size,self.depth+1)

    class MCTSNode: pass  # unused

    def choose_team(self, roster, current_team, log, max_team_size):
        state = MCTSTeamBuildPolicy.MCTSState(current_team, roster, log, max_team_size, 0)
        return self.call_llm(state)

    def call_llm(self, state):
        prompt  = self.build_prompt(state)
        try:
            idxs = query_llm(prompt)
            if len(idxs) != state.max_team_size:
                raise ValueError(f"indices inválidos: {idxs}")
            return idxs
        except Exception:
            logging.exception("Fallback aleatorio:")
            return random.sample(range(len(state.roster)), state.max_team_size)

    def build_prompt(self, roster, current_team, veredict):
        # same as before...
        items = [f"    {i}: {fmt_pokemon_species(sp)}" for i,sp in enumerate(roster)]
        roster_str = ",\n".join(items)
        team_str   = ", ".join(str(i) for i in current_team)
        return (
            "  \"Roster\": [\n" + roster_str + "\n  ],\n"
            f"  \"Team\": [{team_str}],\n"
            f"  \"Veredict\": {veredict}\n"
            "}\n"
        )

    def decision(self, roster, meta, max_team_size, max_pkm_moves, n_active):
        # 1) pick what to pass
        if self.last_team is None:
            current_team, veredict = list(range(max_team_size)), 0
        else:
            current_team, veredict = self.last_team, 1

        logging.info("Inicio decision; team actual: %s", current_team)

        # 2) ask LLM
        prompt = self.build_prompt(roster, current_team, veredict)
        idxs   = query_llm(prompt) or random.sample(range(len(roster)), max_team_size)
        logging.info("Índices elegidos: %s", idxs)

        # 3) save for next round
        self.last_team = idxs

        # 4) dump RAG.txt
        with open("RAG.txt","w") as f:
            f.write("ROSTER:\n")
            for i,sp in enumerate(roster):
                f.write(f"{i}: {fmt_pokemon_species(sp)}\n")
            f.write("\nLAST TEAM INDICES: " + ", ".join(map(str,idxs)) + "\n")
            f.write("LAST TEAM SPECIES:\n")
            for i in idxs:
                f.write(f"{i}: {fmt_pokemon_species(roster[i])}\n")

        # 5) build and return TeamBuildCommand
        ivs = (31,)*6
        cmds=[]
        for i in idxs:
            sp   = roster[i]
            mv   = list(range(len(sp.moves)))[:max_pkm_moves]
            ev   = tuple(multinomial(510, [1/6]*6, size=1)[0])
            nat  = Nature(random.randrange(len(Nature)))
            cmds.append((i, ev, ivs, nat, mv))
            logging.debug("CMD %d: %s", i, cmds[-1])

        return cmds

class RAG_Competitor(Competitor):
    def __init__(self,name="RAG_Competitor"):
        self.__name           = name
        self.__battle_policy  = RandomBattlePolicy()
        self.__selection_policy = RandomSelectionPolicy()
        self.__team_build_policy = MCTSTeamBuildPolicy(mcts_iterations=50)

    @property
    def battle_policy(self):   return self.__battle_policy
    @property
    def selection_policy(self):return self.__selection_policy
    @property
    def team_build_policy(self):return self.__team_build_policy
    @property
    def name(self):           return self.__name

# — test block —
if __name__ == "__main__":
    from vgc2.util.generator import gen_move_set, gen_pkm_roster
    mv   = gen_move_set(100)
    roster = gen_pkm_roster(50,mv)
    comp  = RAG_Competitor()
    _ = comp.team_build_policy.decision(roster, {}, 3, 4, 2)
    print("RAG.txt generado en template/RAG.txt")
