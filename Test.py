from numpy import array

from vgc.pkm_engine.team import Team
from vgc.pkm_engine.threshold_calculator import move_hit_threshold
from vgc.pkm_engine.battle_engine import BattleEngine
from vgc.pkm_engine.modifiers import Status, Category, Stat
from vgc.pkm_engine.move import Move

from vgc.pkm_engine.nature import Nature
from vgc.pkm_engine.pokemon import PokemonSpecies, Pokemon, BattlingPokemon, PokemonView
from vgc.pkm_engine.typing import Type
from vgc.util.encoding import encode_move, EncodeContext

m = Move(Type.FIRE, 60, 1., 10, Category.PHYSICAL, toggle_trickroom=True)
print(m)
ps = PokemonSpecies((100, 100, 100, 100, 100, 100), [Type.PSYCHIC], [m])
print(ps)
p = Pokemon(ps, [0], nature=Nature.TIMID)
print(p)
bp = BattlingPokemon(p)
bp.status = Status.PARALYZED
print(bp)
p2 = Pokemon(ps, [], nature=Nature.GENTLE)
print(p2)
ps.edit((80,) * 6, [Type.WATER], [])
print(ps)
print(p)
print(p2)
bp2 = BattlingPokemon(p2)
bp.boosts[Stat.ACCURACY] = 1
bp2.boosts[Stat.EVASION] = 2
print(move_hit_threshold(bp.battling_moves[0].constants, bp, bp2))
be = BattleEngine((Team([p]), Team([p2])))
print(be)
pv = PokemonView(p)
print(p)
print(pv)
p.on_move_used(0)
print(pv)
pv.hide()
print(pv)
t = Team([p, p2])
print(t)
e = array([0.] * 55)
ctx = EncodeContext()
size = encode_move(e, m, ctx)
print(size, e)
