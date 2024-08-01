import numpy as np

from utils import print_bitboard, print_bitboard_with_files_ranks

RED_SIDE = 0x1FFFFFFFFFFF
BLACK_SIDE = 0x3FFFFFFFFFFE00000000000
BOARD = RED_SIDE | BLACK_SIDE
KING_AREA = 0x70381C0000000000E07038
RED = 0
BLACK = 1

NOT_A_FILE = 0x1FEFF7FBFDFEFF7FBFDFEFF
NOT_I_FILE = 0x3FDFEFF7FBFDFEFF7FBFDFE
NOT_9_RANK = 0x1FFFFFFFFFFFFFFFFFFFF
NOT_0_RANK = 0x3FFFFFFFFFFFFFFFFFFFE00

DIAGONAL_DIRECTIONS = [8, 10, -10, -8]
DIRECTIONS = [9, 1, -1, -9]


class Board:
    def __init__(self):
        self.red_pieces = 0
        self.black_pieces = 0
        self.turn_no = 0
        self.red_pawns = 0
        self.black_pawns = 0
        self.red_cannons = 0
        self.black_cannons = 0
        self.red_rooks = 0
        self.red_horses = 0
        self.red_elephants = 0
        self.red_advisors = 0
        self.red_king = 0
        self.black_rooks = 0
        self.black_horses = 0
        self.black_elephants = 0
        self.black_advisors = 0
        self.black_king = 0
        self.turn = RED
        self.reset()
        self.mask = [1 << i for i in range(90)]
        self.pawns_actions = [[0 for _ in range(90)] for _ in range(2)]
        self.advisor_actions = [0 for _ in range(90)]
        self.king_actions = [0 for _ in range(90)]
        self.horse_blockers = [0 for _ in range(90)]
        self.elephant_blockers = [0 for _ in range(90)]
        self.rook_blockers = [0 for _ in range(90)]
        self.cannon_blockers = [0 for _ in range(90)]
        self.initialize_patterns()
        for i, action in enumerate(self.rook_blockers):
            if action:
                print_bitboard(action)
                print(i)

    def initialize_patterns(self):
        self.initialize_pawn_actions()
        self.initialize_advisor_actions()
        self.initialize_king_actions()
        self.initialize_horse_blockers()
        self.initialize_rook_cannon_blockers()

    def reset(self):
        self.turn = RED
        self.turn_no = 0
        self.red_pawns = 0xAA8000000
        self.black_pawns = 0x5540000000000000
        self.red_cannons = 0x2080000
        self.black_cannons = 0x41
        self.red_rooks = 0x101
        self.red_horses = 0x82
        self.red_elephants = 0x44
        self.red_advisors = 0x28
        self.red_king = 4
        self.black_rooks = 0x2020000
        self.black_horses = 0x1040000
        self.black_elephants = 0x880000
        self.black_advisors = 0x500000
        self.black_king = 85
        self.red_pieces = 0xAAA0801FF
        self.black_pieces = 0x3FE00415540000000000000

    def load_fen(self, fen: str):
        bb_dict = {'p': 0,
                   'r': 0,
                   'b': 0,
                   'n': 0,
                   'a': 0,
                   'k': 0,
                   'c': 0,
                   'P': 0,
                   'R': 0,
                   'B': 0,
                   'N': 0,
                   'A': 0,
                   'K': 0,
                   'C': 0}
        fen_sector = fen.split()
        positions = fen_sector[0]
        self.turn_no = fen_sector[5]
        if fen_sector[1] == 'b':
            self.turn = BLACK
        else:
            self.turn = RED
        pos = 89
        for c in positions:
            if c == "/":
                continue
            if c.isdigit():
                pos -= int(c)
            else:
                bb_dict[c] |= 1 << pos
                pos -= 1

        self.red_pawns = bb_dict['P']
        self.black_pawns = bb_dict['p']
        self.red_cannons = bb_dict['C']
        self.black_cannons = bb_dict['c']
        self.red_rooks = bb_dict['R']
        self.red_horses = bb_dict['N']
        self.red_elephants = bb_dict['B']
        self.red_advisors = bb_dict['A']
        self.red_king = bb_dict['K']
        self.black_rooks = bb_dict['r']
        self.black_horses = bb_dict['n']
        self.black_elephants = bb_dict['b']
        self.black_advisors = bb_dict['a']
        self.black_king = bb_dict['k']

    def initialize_pawn_actions(self):
        temp = 0
        for i in range(27, 90):
            self.pawns_actions[0][i] |= (self.mask[i] & NOT_9_RANK) << 9
            if self.mask[i] & BLACK_SIDE:
                self.pawns_actions[RED][i] |= (self.mask[i] & NOT_A_FILE) << 1
                self.pawns_actions[RED][i] |= (self.mask[i] & NOT_I_FILE) >> 1
        for i in range(62, -1, -1):
            self.pawns_actions[BLACK][i] |= (self.mask[i] & NOT_0_RANK) >> 9
            if self.mask[i] & RED_SIDE:
                self.pawns_actions[BLACK][i] |= (self.mask[i] & NOT_A_FILE) << 1
                self.pawns_actions[BLACK][i] |= (self.mask[i] & NOT_I_FILE) >> 1

    def initialize_advisor_actions(self):
        for i in range(90):
            action = 0
            if self.mask[i] & KING_AREA:
                for direction in DIAGONAL_DIRECTIONS:
                    action |= shift(direction, self.mask[i])
                action &= KING_AREA
                self.advisor_actions[i] = action

    def initialize_king_actions(self):
        for i in range(90):
            action = 0
            if self.mask[i] & KING_AREA:
                for direction in DIRECTIONS:
                    action |= shift(direction, self.mask[i])
                action &= KING_AREA
                self.king_actions[i] = action

    def initialize_horse_blockers(self):
        for i in range(90):
            blocker = 0
            for direction in DIRECTIONS:
                blocker |= shift(direction, self.mask[i])
            blocker &= BOARD
            self.horse_blockers[i] = blocker

    def initialize_elephant_blockers(self):
        for i in range(90):
            blocker = 0
            for direction in DIAGONAL_DIRECTIONS:
                blocker |= shift(direction, self.mask[i])
            blocker &= BOARD
            self.elephant_blockers[i] = blocker

    def initialize_rook_cannon_blockers(self):
        for i in range(90):
            file_mask = (~NOT_I_FILE & BOARD) << get_x(i) & BOARD & ~self.mask[i] & NOT_9_RANK & NOT_0_RANK
            rank_mask = (~NOT_0_RANK & BOARD) << get_y(i) * 9 & BOARD & ~self.mask[i] & NOT_A_FILE & NOT_I_FILE
            self.rook_blockers[i] = file_mask | rank_mask
            self.cannon_blockers[i] = file_mask | rank_mask

    def generate_elephant_actions(self, index, blocker):
        action = 0
        for direction in DIAGONAL_DIRECTIONS:
            elephant_eye = shift(direction, self.mask[index])
            if elephant_eye & blocker:
                continue
            action |= shift(direction, elephant_eye)
        return action


def get_x(index):
    return index % 9


def get_y(index):
    return index // 9


def shift(direction, bitboard):
    if direction > 0:
        return (bitboard << direction) & BOARD
    return (bitboard >> -direction) & BOARD


board = Board()
