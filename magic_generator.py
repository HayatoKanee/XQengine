from random import Random
import pickle

from utils import UPPER_MASK, LOWER_MASK, DIAGONAL_DIRECTIONS, shift, MASK, DIRECTIONS, Direction, BOARD, count_bits, \
    get_ls1b_index, pop_bit, RED, BLACK_SIDE, BLACK, RED_SIDE, KING_AREA, RANK_0, get_y, FILE_A, get_x


class Magic:
    def __init__(self):
        self.mask = 0
        self.magic = 0
        # It costs me a lot of time to figure out we need the second magic number..
        self.high_magic = 0
        self.rshift = 0
        self.attacks = []

    def get_key(self, occupancy):
        relevant_occupancy = occupancy & self.mask
        return ((int((relevant_occupancy & UPPER_MASK) * self.high_magic >> 64) + int(
            ((relevant_occupancy & LOWER_MASK) * self.magic))) & LOWER_MASK) >> self.rshift

    def attack(self, occupancy):
        index = self.get_key(occupancy)
        return self.attacks[index]


def generate_elephant_actions(index, blocker):
    action = 0
    for direction in DIAGONAL_DIRECTIONS:
        elephant_eye = shift(direction, MASK[index])
        if elephant_eye & blocker:
            continue
        action |= shift(direction, elephant_eye)
    return action


def generate_horse_actions(index, blocker):
    action = 0

    invalid_action = 0
    for direction in DIRECTIONS:
        invalid_action |= shift(direction, MASK[index])
    for direction in DIRECTIONS:
        intermediate_step = shift(direction, MASK[index])
        if not intermediate_step & blocker:
            for next_direction in DIAGONAL_DIRECTIONS:
                final_pos = shift(next_direction, intermediate_step)
                if not final_pos & invalid_action:
                    action |= final_pos
    return action


def generate_rook_horizontal_actions(index, blocker):
    action = 0
    for direction in [Direction.EAST, Direction.WEST]:
        pos = MASK[index]
        while not pos & blocker and pos & BOARD:
            pos = shift(direction, pos)
            action |= pos
    return action


def generate_rook_vertical_actions(index, blocker):
    action = 0
    for direction in [Direction.NORTH, Direction.SOUTH]:
        pos = MASK[index]
        while not pos & blocker and pos & BOARD:
            pos = shift(direction, pos)
            action |= pos
    return action


def generate_cannon_horizontal_actions(index, blocker):
    action = 0
    for direction in [Direction.EAST, Direction.WEST]:
        pos = MASK[index]
        while True:
            pos = shift(direction, pos)
            if pos & blocker or not pos & BOARD:
                break
            action |= pos
        while True:
            pos = shift(direction, pos)
            if pos & blocker:
                action |= pos
                break
            if not pos & BOARD:
                break
    return action


def generate_cannon_vertical_actions(index, blocker):
    action = 0
    for direction in [Direction.NORTH, Direction.SOUTH]:
        pos = MASK[index]
        while True:
            pos = shift(direction, pos)
            if pos & blocker or not pos & BOARD:
                break
            action |= pos
        while True:
            pos = shift(direction, pos)
            if pos & blocker:
                action |= pos
                break
            if not pos & BOARD:
                break
    return action


def set_occupancy(index, mask):
    occupancy = 0
    for i in range(count_bits(mask)):
        pos = get_ls1b_index(mask)
        mask = pop_bit(mask, pos)
        if index & (1 << i):
            occupancy |= MASK[pos]
    return occupancy


class MagicGenerator:

    def __init__(self):
        self.pawns_actions = [[0 for _ in range(100)] for _ in range(2)]
        self.advisor_actions = [0 for _ in range(100)]
        self.king_actions = [0 for _ in range(100)]
        self.horse_magics = [Magic() for _ in range(100)]
        self.elephant_magics = [Magic() for _ in range(100)]
        self.rook_rank_magics = [Magic() for _ in range(100)]
        # Splitting rank and file helps the magic number generation, I guess we can still do it even without splitting
        self.rook_file_magics = [Magic() for _ in range(100)]
        self.cannon_rank_magics = [Magic() for _ in range(100)]
        self.cannon_file_magics = [Magic() for _ in range(100)]
        self.initialize_actions()

    def initialize_pawn_actions(self):
        for i in range(30, 100):
            self.pawns_actions[RED][i] |= shift(Direction.NORTH, MASK[i])
            if MASK[i] & BLACK_SIDE:
                self.pawns_actions[RED][i] |= shift(Direction.WEST, MASK[i])
                self.pawns_actions[RED][i] |= shift(Direction.EAST, MASK[i])
        for i in range(68, -1, -1):
            self.pawns_actions[BLACK][i] |= shift(Direction.SOUTH, MASK[i])
            if MASK[i] & RED_SIDE:
                self.pawns_actions[BLACK][i] |= shift(Direction.WEST, MASK[i])
                self.pawns_actions[BLACK][i] |= shift(Direction.EAST, MASK[i])

    def initialize_advisor_actions(self):
        for i in range(100):
            action = 0
            if MASK[i] & KING_AREA:
                for direction in DIAGONAL_DIRECTIONS:
                    action |= shift(direction, MASK[i])
                action &= KING_AREA
                self.advisor_actions[i] = action

    def initialize_king_actions(self):
        for i in range(100):
            action = 0
            if MASK[i] & KING_AREA:
                for direction in DIRECTIONS:
                    action |= shift(direction, MASK[i])
                action &= KING_AREA
                self.king_actions[i] = action

    def initialize_horse_magics(self):
        for i in range(100):
            blocker = 0
            for direction in DIRECTIONS:
                blocker |= shift(direction, MASK[i])
            self.horse_magics[i].mask = blocker

    def initialize_elephant_magics(self):
        for i in range(100):
            blocker = 0
            for direction in DIAGONAL_DIRECTIONS:
                blocker |= shift(direction, MASK[i])
            blocker &= BOARD
            self.elephant_magics[i].mask = blocker

    def initialize_rook_cannon_magics(self):
        for i in range(100):
            if MASK[i]:
                rank = RANK_0 << (10 * get_y(i)) & BOARD & ~MASK[i]
                file = FILE_A << get_x(i) & BOARD & ~MASK[i]
                self.rook_rank_magics[i].mask = rank
                self.rook_file_magics[i].mask = file
                self.cannon_rank_magics[i].mask = rank
                self.cannon_file_magics[i].mask = file

    def generate_magic_numbers(self, index, action_generator, magic, addition_hash_space=0, writing_to_disk=False):
        file_name = 'magics/' + action_generator.__name__.split('_')[1] + '_' + action_generator.__name__.split('_')[
            2] + '.txt'
        if not MASK[index] or magic.mask == 0:
            if writing_to_disk:
                with open(file_name, 'a') as f:
                    f.write("0x0 0x0\n")
            return
        mask = magic.mask
        count = count_bits(mask)
        attack_table_size = 1 << (count + addition_hash_space)
        magic.rshift = 64 - (count + addition_hash_space)
        occupancies = [0 for _ in range(attack_table_size)]
        attacks = [0 for _ in range(attack_table_size)]
        for i in range(attack_table_size):
            occupancies[i] = set_occupancy(i, mask)
            attacks[i] = action_generator(index, occupancies[i])
        random = Random()
        fail = True
        i = 0
        max_j = 0
        j = 0
        while fail:
            i += 1
            if i % 1000000 == 0:
                print(
                    f'Generating magics for {action_generator.__name__}[{index}]: {i}iterations, best result: {max_j}, target = {attack_table_size}')
            magic.magic = random.getrandbits(64)
            magic.high_magic = random.getrandbits(64)
            used_attacks = [0 for _ in range(attack_table_size)]
            max_j = max(max_j, j)
            j = 0
            fail = False
            while not fail and j < attack_table_size:
                key = magic.get_key(occupancies[j])
                if not used_attacks[key]:
                    used_attacks[key] = attacks[j]
                elif used_attacks[key] != attacks[j]:
                    fail = True
                j += 1
            if not fail:
                magic.attacks = used_attacks
                print(
                    f'These two hexes are magic numbers for {action_generator.__name__}[{index}], using {i} iterations')
                print(hex(magic.magic), hex(magic.high_magic))
                if writing_to_disk:
                    with open(file_name, 'a') as f:
                        f.writelines(f"{hex(magic.magic)} {hex(magic.high_magic)}\n")
                return magic.magic, magic.high_magic

    def initialize_actions(self):
        self.initialize_pawn_actions()
        self.initialize_advisor_actions()
        self.initialize_king_actions()
        self.initialize_horse_magics()
        self.initialize_elephant_magics()
        self.initialize_rook_cannon_magics()

    def generate_all_magics(self):
        for i in range(0, 100):
            self.generate_magic_numbers(i, generate_rook_vertical_actions,
                                        self.rook_file_magics[i], 1, False)
            self.generate_magic_numbers(i, generate_rook_horizontal_actions,
                                        self.rook_rank_magics[i], 0, False)
            self.generate_magic_numbers(i, generate_cannon_vertical_actions,
                                        self.cannon_file_magics[i], 2, False)
            self.generate_magic_numbers(i, generate_cannon_horizontal_actions,
                                        self.cannon_rank_magics[i], 0, False)
            self.generate_magic_numbers(i, generate_horse_actions, self.horse_magics[i], 0, False)
            self.generate_magic_numbers(i, generate_elephant_actions, self.elephant_magics[i], 0, False)

    def save_to_file(self):
        with open('magic_numbers.pkl', 'wb') as f:
            pickle.dump(self, f)
        print("MagicGenerator saved to magic_numbers.pkl")

    def load_magic_numbers(self, file_name, magic_list):
        with open('magics/' + file_name, 'r') as f:
            for i in range(100):
                if i % 9 == 0:
                    continue
                line = f.readline()
                magic_numbers = line.split()
                magic_list[i].magic = int(magic_numbers[0], 0)
                magic_list[i].high_magic = int(magic_numbers[1], 0)

    def generate_all_magics_with_pre_calculated_magic_numbers(self):
        self.load_magic_numbers('rook_horizontal.txt', self.rook_rank_magics)
        self.load_magic_numbers('rook_vertical.txt', self.rook_file_magics)
        self.load_magic_numbers('elephant.txt', self.elephant_magics)
        self.load_magic_numbers('horse.txt', self.horse_magics)
        self.load_magic_numbers('cannon_horizontal.txt', self.cannon_rank_magics)
        self.load_magic_numbers('cannon_vertical.txt', self.cannon_file_magics)
        for i in range(100):
            self.generate_attacks_with_pre_calculated_magic_numbers(i, generate_rook_vertical_actions,
                                                                    self.rook_file_magics[i], 1)
            self.generate_attacks_with_pre_calculated_magic_numbers(i, generate_rook_horizontal_actions,
                                                                    self.rook_rank_magics[i])
            self.generate_attacks_with_pre_calculated_magic_numbers(i, generate_elephant_actions,
                                                                    self.elephant_magics[i])
            self.generate_attacks_with_pre_calculated_magic_numbers(i, generate_horse_actions, self.horse_magics[i])
            self.generate_attacks_with_pre_calculated_magic_numbers(i, generate_cannon_horizontal_actions,
                                                                    self.cannon_rank_magics[i])
            self.generate_attacks_with_pre_calculated_magic_numbers(i, generate_cannon_vertical_actions,
                                                                    self.cannon_file_magics[i], 2)

    def generate_attacks_with_pre_calculated_magic_numbers(self, index, action_generator, magic, addition_hash_space=0):
        if not MASK[index] or magic.mask == 0:
            return
        mask = magic.mask
        count = count_bits(mask)
        attack_table_size = 1 << (count + addition_hash_space)
        magic.rshift = 64 - (count + addition_hash_space)
        occupancies = [0 for _ in range(attack_table_size)]
        attacks = [0 for _ in range(attack_table_size)]
        for i in range(attack_table_size):
            occupancies[i] = set_occupancy(i, mask)
            attacks[i] = action_generator(index, occupancies[i])
        used_attacks = [0 for _ in range(attack_table_size)]
        for i in range(attack_table_size):
            key = magic.get_key(occupancies[i])
            used_attacks[key] = attacks[i]
        magic.attacks = used_attacks


magic_generator = MagicGenerator()
magic_generator.generate_all_magics()
magic_generator.save_to_file()
