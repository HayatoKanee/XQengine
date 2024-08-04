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
        self.generate_all_magics()

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

    def generate_magic_numbers(self, index, action_generator, magic, addition_hash_space=0):
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
        random = Random()
        fail = True
        while fail:
            magic.magic = random.getrandbits(64)
            magic.high_magic = random.getrandbits(64)
            used_attacks = [0 for _ in range(attack_table_size)]
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
                return magic.magic
        print('nope, not working')

    def initialize_actions(self):
        self.initialize_pawn_actions()
        self.initialize_advisor_actions()
        self.initialize_king_actions()
        self.initialize_horse_magics()
        self.initialize_elephant_magics()
        self.initialize_rook_cannon_magics()

    def generate_all_magics(self):
        for i in range(100):
            self.generate_magic_numbers(i, generate_rook_vertical_actions,
                                        self.rook_file_magics[i], 0)
            self.generate_magic_numbers(i, generate_rook_horizontal_actions,
                                        self.rook_rank_magics[i], 0)
            self.generate_magic_numbers(i, generate_cannon_vertical_actions,
                                        self.cannon_file_magics[i], 0)
            self.generate_magic_numbers(i, generate_cannon_horizontal_actions,
                                        self.cannon_rank_magics[i], 0)
            self.generate_magic_numbers(i, generate_horse_actions, self.horse_magics[i], 0)
            self.generate_magic_numbers(i, generate_elephant_actions, self.elephant_magics[i], 0)

    def save_to_file(self):
        with open('magic_numbers.pkl', 'wb') as f:
            pickle.dump(self, f)
        print("MagicGenerator saved to magic_numbers.pkl")
