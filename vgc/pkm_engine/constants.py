from vgc.pkm_engine.modifiers import PermStat
from vgc.pkm_engine.nature import Nature

DAMAGE_MULTIPLICATION_ARRAY = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 / 2, 0, 1, 1, 1 / 2, 1, 1],
                               [1, 1 / 2, 1 / 2, 1, 2, 2, 1, 1, 1, 1, 1, 2, 1 / 2, 1, 1 / 2, 1, 2, 1, 1],
                               [1, 2, 1 / 2, 1, 1 / 2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1 / 2, 1, 1, 1, 1],
                               [1, 1, 2, 1 / 2, 1 / 2, 1, 1, 1, 0, 2, 1, 1, 1, 1, 1 / 2, 1, 1, 1, 1],
                               [1, 1 / 2, 2, 1, 1 / 2, 1, 1, 1 / 2, 2, 1 / 2, 1, 1 / 2, 2, 1, 1 / 2, 1, 1 / 2, 1, 1],
                               [1, 1 / 2, 1 / 2, 1, 2, 1 / 2, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 1 / 2, 1, 1],
                               [2, 1, 1, 1, 1, 2, 1, 1 / 2, 1, 1 / 2, 1 / 2, 1 / 2, 2, 0, 1, 2, 2, 1 / 2, 1],
                               [1, 1, 1, 1, 2, 1, 1, 1 / 2, 1 / 2, 1, 1, 1, 1 / 2, 1 / 2, 1, 1, 0, 2, 1],
                               [1, 2, 1, 2, 1 / 2, 1, 1, 2, 1, 0, 1, 1 / 2, 2, 1, 1, 1, 2, 1, 1],
                               [1, 1, 1, 1 / 2, 2, 1, 2, 1, 1, 1, 1, 2, 1 / 2, 1, 1, 1, 1 / 2, 1, 1],
                               [1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1 / 2, 1, 1, 1, 1, 0, 1 / 2, 1, 1],
                               [1, 1 / 2, 1, 1, 2, 1, 1 / 2, 1 / 2, 1, 1 / 2, 2, 1, 1, 1 / 2, 1, 2, 1 / 2, 1 / 2, 1],
                               [1, 2, 1, 1, 1, 2, 1 / 2, 1, 1 / 2, 2, 1, 2, 1, 1, 1, 1, 1 / 2, 1, 1],
                               [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1 / 2, 1, 1, 1],
                               [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1 / 2, 0, 1],
                               [1, 1, 1, 1, 1, 1, 1 / 2, 1, 1, 1, 2, 1, 1, 2, 1, 1 / 2, 1, 1 / 2, 1],
                               [1, 1 / 2, 1 / 2, 1 / 2, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1 / 2, 2, 1],
                               [1, 1 / 2, 1, 1, 1, 1, 2, 1 / 2, 1, 1, 1, 1, 1, 1, 2, 2, 1 / 2, 1, 1],
                               [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

BOOST_MULTIPLIER_LOOKUP = {
    -6: 2 / 8,
    -5: 2 / 7,
    -4: 2 / 6,
    -3: 2 / 5,
    -2: 2 / 4,
    -1: 2 / 3,
    0: 2 / 2,
    1: 3 / 2,
    2: 4 / 2,
    3: 5 / 2,
    4: 6 / 2,
    5: 7 / 2,
    6: 8 / 2
}

TERRAIN_DAMAGE_BOOST = 1.3

NATURES = {
    Nature.LONELY: {
        'plus': PermStat.ATTACK,
        'minus': PermStat.DEFENSE
    },
    Nature.ADAMANT: {
        'plus': PermStat.ATTACK,
        'minus': PermStat.SPECIAL_ATTACK
    },
    Nature.NAUGHTY: {
        'plus': PermStat.ATTACK,
        'minus': PermStat.SPECIAL_DEFENSE
    },
    Nature.BRAVE: {
        'plus': PermStat.ATTACK,
        'minus': PermStat.SPEED
    },
    Nature.BOLD: {
        'plus': PermStat.DEFENSE,
        'minus': PermStat.ATTACK
    },
    Nature.IMPISH: {
        'plus': PermStat.DEFENSE,
        'minus': PermStat.SPECIAL_ATTACK
    },
    Nature.LAX: {
        'plus': PermStat.DEFENSE,
        'minus': PermStat.SPECIAL_DEFENSE
    },
    Nature.RELAXED: {
        'plus': PermStat.DEFENSE,
        'minus': PermStat.SPEED
    },
    Nature.MODEST: {
        'plus': PermStat.SPECIAL_ATTACK,
        'minus': PermStat.ATTACK
    },
    Nature.MILD: {
        'plus': PermStat.SPECIAL_ATTACK,
        'minus': PermStat.DEFENSE
    },
    Nature.RASH: {
        'plus': PermStat.SPECIAL_ATTACK,
        'minus': PermStat.SPECIAL_DEFENSE
    },
    Nature.QUIET: {
        'plus': PermStat.SPECIAL_ATTACK,
        'minus': PermStat.SPEED
    },
    Nature.CALM: {
        'plus': PermStat.SPECIAL_DEFENSE,
        'minus': PermStat.ATTACK
    },
    Nature.GENTLE: {
        'plus': PermStat.SPECIAL_DEFENSE,
        'minus': PermStat.DEFENSE
    },
    Nature.CAREFUL: {
        'plus': PermStat.SPECIAL_DEFENSE,
        'minus': PermStat.SPECIAL_ATTACK
    },
    Nature.SASSY: {
        'plus': PermStat.SPECIAL_DEFENSE,
        'minus': PermStat.SPEED
    },
    Nature.TIMID: {
        'plus': PermStat.SPEED,
        'minus': PermStat.ATTACK
    },
    Nature.HASTY: {
        'plus': PermStat.SPEED,
        'minus': PermStat.DEFENSE
    },
    Nature.JOLLY: {
        'plus': PermStat.SPEED,
        'minus': PermStat.SPECIAL_ATTACK
    },
    Nature.NAIVE: {
        'plus': PermStat.SPEED,
        'minus': PermStat.SPECIAL_DEFENSE
    },
}
