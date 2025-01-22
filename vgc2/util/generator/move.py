from random import sample

from numpy import clip
from numpy.random import choice, normal, rand

from vgc2.pkm_engine.modifiers import Category
from vgc2.pkm_engine.move import Move
from vgc2.pkm_engine.typing import Type


def gen_move() -> Move:
    category = Category(choice(len(Category), 1, False))
    base_power = 0 if category == Category.OTHER else clip(int(normal(100, 0.2, 1)[0]), 0, 140)
    effect = rand(0, 1) if category == Category.OTHER else -1

    return Move(
        pkm_type=Type(choice(len(Type), 1, False)),
        base_power=base_power,
        accuracy=1. if rand(0, 1) < .5 else rand(0, 1),
        max_pp=clip(int(normal(10, 2, 1)[0]), 5, 20),
        category=category,
        priority=1 if rand(0, 1) < .3 else 0,
        force_switch=0 <= effect < 1 / 17,
        self_switch=1 / 17 <= effect < 2 / 17,
        ignore_evasion=2 / 17 <= effect < 3 / 17,
        protect=3 / 17 <= effect < 4 / 17,
        boosts=boosts,
        heal=heal,
        recoil=recoil,
        weather_start=weather,
        field_start=field,
        toggle_trickroom=9 / 17 <= effect < 10 / 17,
        change_type=10 / 17 <= effect < 11 / 17,
        toggle_reflect=11 / 17 <= effect < 12 / 17,
        toggle_lightscreen=12 / 17 <= effect < 13 / 17,
        toggle_tailwind=13 / 17 <= effect < 14 / 17,
        hazard=hazard,
        status=status,
        disable=16 / 17 <= effect < 1
    )


def gen_move_set(n: int) -> list[Move]:
    moves: list[Move] = []
    i = 0
    while i < n:
        moves += [gen_move()]
        i += 1
    return moves


def gen_move_subset(n: int,
                    moves: list[Move]) -> list[Move]:
    return sample(moves, min(n, len(moves)))
