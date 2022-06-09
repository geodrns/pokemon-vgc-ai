from copy import deepcopy

from vgc.datatypes.Objects import PkmTeamPrediction, PkmTeam, null_pkm, Pkm
from vgc.engine.PkmBattleEnv import PkmBattleEnv


def _set_moves(pkm: Pkm, prediction: Pkm):
    for i in range(len(pkm.moves)):
        if not pkm.moves[i].revealed:
            if prediction is not None:
                pkm.moves[i] = prediction.moves[i]
            else:
                pkm.moves[i] = null_pkm.moves[i]


def _set_pkm(pkm: Pkm, prediction: Pkm):
    if pkm.revealed:
        _set_moves(pkm, prediction)
    elif prediction is not None:
        pkm.type = prediction.type
        pkm.hp = prediction.hp
        _set_moves(pkm, prediction)
    else:
        pkm.type = null_pkm.type
        pkm.hp = null_pkm.hp
        _set_moves(pkm, null_pkm)


def state_prediction(base_env: PkmBattleEnv, player: int, team_prediction: PkmTeamPrediction = None) -> PkmBattleEnv:
    env = PkmBattleEnv((deepcopy(base_env.teams[0]), deepcopy(base_env.teams[1])), deepcopy(base_env.weather))
    env.n_turns_no_clear = base_env.n_turns_no_clear
    env.turn = base_env.turn
    env.winner = base_env.winner
    # hidde information and replace with prediction information
    opp_team: PkmTeam = env.game_state[player].teams[1]
    _set_pkm(opp_team.active, team_prediction.active)
    for i in range(len(opp_team.party)):
        _set_pkm(opp_team.party[i], team_prediction.party[i])
    return env
