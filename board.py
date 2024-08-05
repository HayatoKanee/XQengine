import os
import pickle

from magic_generator import MagicGenerator
from utils import *


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
        self.end = False
        self.pawns_actions = []
        self.advisor_actions = []
        self.king_actions = []
        self.horse_magics = []
        self.elephant_magics = []
        self.rook_rank_magics = []
        self.rook_file_magics = []
        self.cannon_rank_magics = []
        self.cannon_file_magics = []
        self.legal_actions = []
        self.load_magic()

    def load_magic(self):
        if not os.path.exists('magic_numbers.pkl'):
            print("magic_numbers.pkl does not exist. Creating new MagicGenerator instance.")
            magic_generator = MagicGenerator()
            magic_generator.generate_all_magics()
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
        self.end = False
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

    def generate_legal_actions(self):
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
            all_pieces = self.pieces[RED] | self.pieces[BLACK]
            file = FILE_A << x
            relevant_piece = all_pieces & file
            blocker = False
            red_king_found = False
            black_king_found = False
            while not blocker and relevant_piece and not black_king_found:
                ls1b = get_ls1b_index(relevant_piece)
                if ls1b == self.king[RED]:
                    red_king_found = True
                    relevant_piece = pop_bit(relevant_piece, ls1b)
                    continue
                if red_king_found and ls1b != self.king[BLACK]:
                    blocker = True
                    break
                elif red_king_found and ls1b == self.king[BLACK]:
                    black_king_found = True
                relevant_piece = pop_bit(relevant_piece, ls1b)
            if not blocker:
                self.legal_actions[self.king[self.turn]] |= MASK[self.king[get_opponent_colour(self.turn)]]
        for i, action in enumerate(self.legal_actions):
            if action:
                print_bitboard(action)
                print(i)

    def check_action(self, action):
        from_index, to_index = action
        if self.legal_actions[from_index] & MASK[to_index]:
            return True
        return False

    def generate_next_state(self, legal_action):
        # apply the action
        from_index, to_index = legal_action
        opponent_colour = get_opponent_colour(self.turn)
        capture = self.pieces[opponent_colour] & MASK[to_index]
        if capture:
            piece_type = self.convert_index_to_char(to_index).lower()
            if piece_type == 'k':
                self.end = True
            else:
                relevant_attr = convert_char_to_attr_name(piece_type)
                setattr(self, relevant_attr, getattr(self, relevant_attr) ^ MASK[to_index])
            self.pieces[opponent_colour] ^= MASK[to_index]
        piece_type = self.convert_index_to_char(from_index).lower()
        if piece_type == 'k':
            self.king[self.turn] = to_index
        else:
            relevant_attr = convert_char_to_attr_name(piece_type)
            setattr(self, relevant_attr, getattr(self, relevant_attr) ^ MASK[from_index])
            setattr(self, relevant_attr, getattr(self, relevant_attr) ^ MASK[to_index])
        self.pieces[self.turn] ^= MASK[from_index]
        self.pieces[self.turn] ^= MASK[to_index]
        self.turn += 1
        self.turn = opponent_colour

    def convert_index_to_char(self, index):
        piece_mapping = {
            (self.pawns & self.pieces[RED]): 'P',
            (self.pawns & self.pieces[BLACK]): 'p',
            (self.cannons & self.pieces[RED]): 'C',
            (self.cannons & self.pieces[BLACK]): 'c',
            (self.rooks & self.pieces[RED]): 'R',
            (self.rooks & self.pieces[BLACK]): 'r',
            (self.horses & self.pieces[RED]): 'N',
            (self.horses & self.pieces[BLACK]): 'n',
            (self.elephants & self.pieces[RED]): 'B',
            (self.elephants & self.pieces[BLACK]): 'b',
            (self.advisors & self.pieces[RED]): 'A',
            (self.advisors & self.pieces[BLACK]): 'a',
            MASK[self.king[RED]]: 'K',
            MASK[self.king[BLACK]]: 'k'
        }
        for condition, symbol in piece_mapping.items():
            if MASK[index] & condition:
                return symbol
        return '*'

    def __str__(self):
        s = ''
        for i in range(9, -1, -1):
            for j in range(8, -1, -1):
                s += self.convert_index_to_char(j + i * 10)
            s += '\n'
        s = s.rstrip('\n')
        files = "ABCDEFGHI"[::-1]
        ranks = "9876543210"

        output_with_labels = "  " + files + "\n"
        for i, row in enumerate(s.split('\n')):
            output_with_labels += ranks[i] + " " + row + "\n"
        output_with_labels += "  " + files + "\n"

        return output_with_labels
