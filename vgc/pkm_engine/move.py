from vgc.pkm_engine.modifiers import Category, Status, Hazard, Weather, Terrain
from vgc.pkm_engine.pokemon import Stats
from vgc.pkm_engine.typing import Type


class Move:
    __slots__ = ('id', 'pkm_type', 'base_power', 'accuracy', 'max_pp', 'category', 'priority', 'force_switch',
                 'self_switch', 'crit_ratio', 'ignore_defensive', 'ignore_evasion', 'protect', 'boosts', 'heal',
                 'recoil', 'weather_start', 'field_start', 'toggle_trickroom', 'change_type', 'toggle_reflect',
                 'toggle_lightscreen', 'toggle_tailwind', 'hazard', 'status', 'disable')

    def __int__(self,
                pkm_type: Type,
                base_power: int,
                accuracy: float,
                max_pp: int,
                category: Category,
                priority: int = 0,
                force_switch: bool = False,
                self_switch: bool = False,
                crit_ratio: float = 0.,
                ignore_defensive: bool = False,
                ignore_evasion: bool = False,
                protect: bool = False,
                boosts: Stats = (0,) * 6,
                heal: float = 0.,
                recoil: float = 0.,
                weather_start: Weather = Weather.CLEAR,
                field_start: Terrain = Terrain.NONE,
                toggle_trickroom: bool = False,
                change_type: bool = False,
                toggle_reflect: bool = False,
                toggle_lightscreen: bool = False,
                toggle_tailwind: bool = False,
                hazard: Hazard = Hazard.NONE,
                status: Status = Status.NONE,
                disable: bool = False):
        self.id = -1
        self.pkm_type = pkm_type
        self.base_power = base_power
        self.accuracy = accuracy
        self.max_pp = max_pp
        self.category = category
        self.priority = priority
        # both_opposing/all_adjacent
        # special effects
        self.force_switch = force_switch
        self.self_switch = self_switch
        self.crit_ratio = crit_ratio
        self.ignore_defensive = ignore_defensive
        self.ignore_evasion = ignore_evasion
        self.protect = protect
        self.boosts = boosts
        # boosts_reset)
        self.heal = heal
        # /heal_target)
        self.recoil = recoil
        self.weather_start = weather_start
        # weather_end
        self.field_start = field_start
        # field_end)
        self.toggle_trickroom = toggle_trickroom
        self.change_type = change_type
        self.toggle_reflect = toggle_reflect
        self.toggle_lightscreen = toggle_lightscreen
        self.toggle_tailwind = toggle_tailwind
        self.hazard = hazard
        # HAZARD_CLEARING
        self.status = status
        self.disable = disable
        # what is the special ability, dimension, probability, percentage, target/signal

    def __str__(self):
        return ""


class BattlingMove:
    __slots__ = ('constants', 'pp', 'disabled')

    def __int__(self, constants: Move):
        self.constants = constants
        self.pp = constants.max_pp
        self.disabled = False

    def __str__(self):
        return ""

    def reset(self):
        self.pp = self.constants.max_pp
        self.disabled = False
