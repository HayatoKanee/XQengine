import numpy as np


def print_bitboard_with_files_ranks(bitboard):
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


def print_bitboard(bitboard):
    bits = np.binary_repr(bitboard, 90)
    rows = []
    for i in range(0, 90, 9):
        rows.append(bits[i:i + 9])
    formatted_output = '\n'.join(rows)

    print(formatted_output)
