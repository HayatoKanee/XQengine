from bit90 import Bit90


class Board:
    def __init__(self):

        self.all_positions = Bit90(0x5540000AAA0801FF, 0x3FE0041)
        self.red_pawns = Bit90(0xAA8000000)
        self.black_pawns = Bit90(0x5540000000000000)
        self.red_cannons = Bit90(0x2080000)
        self.black_cannons = Bit90(high=0x41)
        self.red_rooks = Bit90(0x101)
        self.red_knights = Bit90(0x82)
        self.red_bishops = Bit90(0x44)
        self.red_advisors = Bit90(0x28)
        self.red_king = Bit90(0x10)
        self.black_rooks = Bit90(high=0x2020000)
        self.black_knights = Bit90(high=0x1040000)
        self.black_bishops = Bit90(high=0x880000)
        self.black_advisors = Bit90(high=0x500000)
        self.black_king = Bit90(high=0x200000)
        self.mask = [Bit90() for _ in range(91)]
        for i in range(91):
            self.mask[i].set_bit(i)
        self.knight_moves = self.generate_knight_moves()


board = Board()
