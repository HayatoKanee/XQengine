from enum import Enum

import numpy as np

# 10 * 10 bit board
RED_SIDE = 0x1FF7FDFF7FDFF
BLACK_SIDE = 0x7FDFF7FDFF7FC000000000000
BOARD = 0x7FDFF7FDFF7FDFF7FDFF7FDFF
KING_AREA = 0xE0380E00000000000380E038
RED = 0
BLACK = 1

FILE_A = 0x40100401004010040100401
RANK_0 = 0x1FF
FILE_I = FILE_A << 8
RANK_9 = RANK_0 << (10 * 9)
MASK = [(1 << i) & BOARD for i in range(100)]


class Direction(Enum):
    def __neg__(self):
        return Direction(-self.value)

    def __add__(self, other):
        return Direction(self.value + other.value)

    NORTH = 10
    EAST = 1
    WEST = -EAST
    SOUTH = -NORTH
    NORTHEAST = NORTH + EAST
    NORTHWEST = NORTH + WEST
    SOUTHWEST = WEST + SOUTH
    SOUTHEAST = EAST + SOUTH


DIAGONAL_DIRECTIONS = [Direction.NORTHEAST, Direction.NORTHWEST, Direction.SOUTHWEST, Direction.SOUTHEAST]
DIRECTIONS = [Direction.NORTH, Direction.EAST, Direction.WEST, Direction.SOUTH]
STARTING_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'

LOWER_MASK = 0xFFFFFFFFFFFFFFFF
UPPER_MASK = 0xFFFFFFFFFFFFFFFF0000000000000000
def get_opponent_colour(colour):
    if colour == BLACK:
        return RED
    return BLACK


# seed = 999999999
#
#
# def get_random_u32_number():
#     number = seed
#     number ^= np.uint32(number) << np.uint32(13)
#     number ^= np.uint32(number) >> np.uint32(17)
#     number ^= np.uint32(number) << np.uint32(5)
#     return number
#
# def get_random_u64_number():
#     n1 = np.uint64(get_random_u32_number()) & np.uint64(0xFFFF)
#     n2 = np.uint64(get_random_u32_number()) & np.uint64(0xFFFF)
#     n3 = np.uint64(get_random_u32_number()) & np.uint64(0xFFFF)
#     n4 = np.uint64(get_random_u32_number()) & np.uint64(0xFFFF)
#     return n1 | (n2 << np.uint64(16)) | (n3 << np.uint64(32)) | (n4 << np.uint64(48))


def print_bitboard_with_files_ranks(bitboard):
    bits = np.binary_repr(bitboard, 100)
    rows = []
    for i in range(0, 100, 10):
        rows.append(bits[i + 1:i + 10])
    formatted_output = '\n'.join(rows)

    # Add file and rank labels
    files = reversed("ABCDEFGHI")
    ranks = "9876543210"

    output_with_labels = "  " + files + "\n"
    for i, row in enumerate(formatted_output.split('\n')):
        output_with_labels += ranks[i] + " " + row + "\n"
    output_with_labels += "  " + files + "\n"

    print(output_with_labels)


def print_bitboard(bitboard):
    bits = np.binary_repr(bitboard, 100)
    rows = []
    for i in range(0, 100, 10):
        rows.append(bits[i + 1:i + 10])
    formatted_output = '\n'.join(rows)

    print(formatted_output)


def print_bitboard_with_hidden_column(bitboard):
    bits = np.binary_repr(bitboard, 100)
    rows = []
    for i in range(0, 100, 10):
        rows.append(bits[i:i + 10])
    formatted_output = '\n'.join(rows)

    print(formatted_output)


def get_x(index):
    return index % 10


def get_y(index):
    return index // 10


def shift(direction, bitboard):
    if direction.value > 0:
        return (bitboard << direction.value) & BOARD
    return (bitboard >> -direction.value) & BOARD


def count_bits(bitboard):
    count = 0
    while bitboard:
        count += 1
        bitboard &= bitboard - 1
    return count
    # return bin(bitboard).count('1')


def get_ls1b_index(bitboard):
    if bitboard:
        return count_bits((bitboard & -bitboard) - 1)
    return -1


def pop_bit(bitboard, index):
    return bitboard & ~MASK[index]
