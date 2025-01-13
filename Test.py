from vgc.pkm_engine.modifiers import Status
from vgc.pkm_engine.nature import Nature
from vgc.pkm_engine.pokemon import PokemonSpecies, Pokemon, BattlingPokemon
from vgc.pkm_engine.typing import Type

ps = PokemonSpecies((100, 100, 100, 100, 100, 100), [Type.PSYCHIC])
print(ps)
p = Pokemon(ps, [], nature=Nature.TIMID)
print(p)
bp = BattlingPokemon(p)
bp.status = Status.PARALYZED
print(bp)
