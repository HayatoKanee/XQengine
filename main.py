import numpy as np


def print_bitboard(bitboard):
    bits = np.binary_repr(bitboard, 90)
    rows = []
    for i in range(0, 90, 9):
        rows.append(bits[i:i + 9])
    formatted_output = '\n'.join(rows)

    # Add file and rank labels
    files = "abcdefghi"
    ranks = "9876543210"

    output_with_labels = "  " + files + "\n"
    for i, row in enumerate(formatted_output.split('\n')):
        output_with_labels += ranks[i] + " " + row + "\n"
    output_with_labels += "  " + files + "\n"

    print(output_with_labels)


class Board:
    def __init__(self):
        self.all_positions = 0x3FE00415540000AAA0801FF
        self.red_pawns = 0xAA8000000
        self.black_pawns = 0x5540000000000000
        self.red_cannons = 0x2080000
        self.black_cannons = 0x41
        self.red_rooks = 0x101
        self.red_horses = 0x82
        self.red_elephants = 0x44
        self.red_advisors = 0x28
        self.red_king = 0x10
        self.black_rooks = 0x2020000
        self.black_horses = 0x1040000
        self.black_elephants = 0x880000
        self.black_advisors = 0x500000
        self.black_king = 0x200000
        self.mask = [0b1 << i for i in range(90)]
        self.red_pawns_actions = [0b0 for _ in range(90)]
        self.black_pawns_actions = [0b0 for _ in range(90)]
        self.generate_pawns_actions()

    def generate_pawns_actions(self):
        # Generate actions for red pawns
        for i in range(27, 90):
            if i <= 44:
                # Only move forward
                if i + 9 < 90:
                    self.red_pawns_actions[i] = self.mask[i + 9]
            else:
                # Move forward and sideways
                actions = 0
                if i + 9 < 90:
                    actions |= self.mask[i + 9]
                if (i % 9) > 0:  # Can move left
                    actions |= self.mask[i - 1]
                if (i % 9) < 8:  # Can move right
                    actions |= self.mask[i + 1]
                self.red_pawns_actions[i] = actions

        # Generate actions for black pawns
        for i in range(62, -1, -1):
            if i >= 45:
                # Only move forward
                if i - 9 >= 0:
                    self.black_pawns_actions[i] = self.mask[i - 9]
            else:
                # Move forward and sideways
                actions = 0
                if i - 9 >= 0:
                    actions |= self.mask[i - 9]
                if (i % 9) > 0:  # Can move left
                    actions |= self.mask[i - 1]
                if (i % 9) < 8:  # Can move right
                    actions |= self.mask[i + 1]
                self.black_pawns_actions[i] = actions

    def


board = Board()
