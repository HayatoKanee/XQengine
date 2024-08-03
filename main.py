import os
import pickle
from random import Random

import numpy as np

from magic_generator import MagicGenerator
from utils import print_bitboard, print_bitboard_with_files_ranks, RED, BLACK, BLACK_SIDE, RED_SIDE, KING_AREA, \
    DIAGONAL_DIRECTIONS, shift, DIRECTIONS, BOARD, get_x, get_y, print_bitboard_with_hidden_column, Direction, FILE_A, \
    RANK_0, RANK_9, FILE_I, count_bits, get_ls1b_index, MASK, pop_bit, get_opponent_colour, STARTING_FEN, UPPER_MASK, \
    LOWER_MASK


class Board:
    def __init__(self):
        self.pieces = [0 for _ in range(2)]
        self.turn_no = 0
        self.pawns = 0
        self.cannons = 0
        self.rooks = 0
        self.horses = 0
        self.elephants = 0
        self.advisors = 0
        self.king = []
        self.turn = RED
        self.reset()
        self.pawns_actions = []
        self.advisor_actions = []
        self.king_actions = []
        self.horse_magics = []
        self.elephant_magics = []
        self.rook_rank_magics = []
        # Splitting rank and file helps the magic number generation, I guess we can still do it even without splitting
        self.rook_file_magics = []
        self.cannon_rank_magics = []
        self.cannon_file_magics = []
        self.legal_actions = []
        self.load_magic()

    def load_magic(self):
        if not os.path.exists('magic_numbers.pkl'):
            print("magic_numbers.pkl does not exist. Creating new MagicGenerator instance.")
            magic_generator = MagicGenerator()
            magic_generator.save_to_file()
        else:
            file = open('magic_numbers.pkl', 'rb')
            magic_generator = pickle.load(file)
            file.close()
        self.pawns_actions = magic_generator.pawns_actions
        self.advisor_actions = magic_generator.advisor_actions
        self.king_actions = magic_generator.king_actions
        self.horse_magics = magic_generator.horse_magics
        self.elephant_magics = magic_generator.elephant_magics
        self.rook_rank_magics = magic_generator.rook_rank_magics
        self.rook_file_magics = magic_generator.rook_file_magics
        self.cannon_rank_magics = magic_generator.cannon_rank_magics
        self.cannon_file_magics = magic_generator.cannon_file_magics

    def reset(self):
        self.load_fen(STARTING_FEN)

    def load_fen(self, fen: str):
        self.pieces[RED] = 0
        self.pieces[BLACK] = 0
        bb_dict = {'p': 0,
                   'r': 0,
                   'b': 0,
                   'n': 0,
                   'a': 0,
                   'k': 0,
                   'c': 0,
                   }

        fen_sector = fen.split()
        positions = fen_sector[0]
        self.turn_no = fen_sector[5]
        if fen_sector[1] == 'b':
            self.turn = BLACK
        else:
            self.turn = RED
        pos = 98
        for c in positions:
            if c == "/":
                pos -= 1
            elif c.isdigit():
                pos -= int(c)
            else:
                bb_dict[c.lower()] |= 1 << pos
                if c.islower():
                    self.pieces[BLACK] |= 1 << pos
                else:
                    self.pieces[RED] |= 1 << pos
                pos -= 1

        self.pawns = bb_dict['p']
        self.cannons = bb_dict['c']
        self.rooks = bb_dict['r']
        self.horses = bb_dict['n']
        self.elephants = bb_dict['b']
        self.advisors = bb_dict['a']
        self.king = [0 for _ in range(2)]
        k = bb_dict['k']
        for i in range(2):
            self.king[i] = get_ls1b_index(k)
            k = pop_bit(k, self.king[i])

    def generate_actions_by_magic(self, pieces, magics, extra_magics=None):
        opponent_colour = get_opponent_colour(self.turn)
        relevant_piece = pieces & self.pieces[self.turn]
        occupancy = self.pieces[self.turn] | self.pieces[opponent_colour]
        count = count_bits(relevant_piece)
        for i in range(count):
            index = get_ls1b_index(relevant_piece)
            relevant_piece = pop_bit(relevant_piece, index)
            action = magics[index].attack(occupancy)
            extra_action = 0
            if extra_magics:
                extra_action = extra_magics[index].attack(occupancy)
            action |= extra_action
            block = action & self.pieces[self.turn]
            legal_action = action ^ block
            self.legal_actions[index] = legal_action

    def generate_normal_actions(self, pieces, actions):
        own_piece = pieces & self.pieces[self.turn]
        count = count_bits(own_piece)
        for i in range(count):
            index = get_ls1b_index(own_piece)
            own_piece = pop_bit(own_piece, index)
            action = actions[index]
            block = action & self.pieces[self.turn]
            legal_action = action ^ block
            self.legal_actions[index] = legal_action

    def get_legal_action(self):
        self.legal_actions = [0 for _ in range(100)]
        self.generate_actions_by_magic(self.cannons, self.cannon_rank_magics, self.cannon_file_magics)
        self.generate_actions_by_magic(self.rooks, self.rook_rank_magics, self.rook_file_magics)
        self.generate_actions_by_magic(self.horses, self.horse_magics)
        self.generate_actions_by_magic(self.elephants, self.elephant_magics)
        self.generate_normal_actions(self.pawns, self.pawns_actions[self.turn])
        self.generate_normal_actions(self.advisors, self.advisor_actions)
        self.generate_normal_actions(MASK[self.king[self.turn]], self.king_actions)
        if get_x(self.king[RED]) == get_x(self.king[BLACK]):
            x = get_x(self.king[RED])
            if count_bits(FILE_A << x & (self.pieces[RED] | self.pieces[BLACK])) == 2:
                self.legal_actions[self.king[self.turn]] = MASK[self.king[get_opponent_colour(self.turn)]]

        for i, action in enumerate(self.legal_actions):
            if action:
                print_bitboard(action)
                print(i)


board = Board()
board.get_legal_action()
