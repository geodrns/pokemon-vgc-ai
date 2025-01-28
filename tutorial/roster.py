from vgc2.util.generator import gen_move_set, gen_pkm_roster


def main():
    move_set = gen_move_set(100)
    roster = gen_pkm_roster(100, move_set)
    print('~ Roster ~')
    for i, p in enumerate(roster):
        print("pokemon " + str(i) + ": " + str(p))


if __name__ == '__main__':
    main()
