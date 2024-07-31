import numpy as np


class Bit90:
    def __init__(self, low=0, high=0):
        self.low = np.uint64(low)  # Lower 64 bits
        self.high = np.uint32(high)  # Higher 26 bits (32-6) for efficiency

    def set_bit(self, pos):
        if pos < 64:
            self.low |= (np.uint64(1) << np.uint64(pos))
        else:
            self.high |= (np.uint32(1) << np.uint32((pos - 64)))

    def clear_bit(self, pos):
        if pos < 64:
            self.low &= ~(np.uint64(1) << np.uint64(pos))
        else:
            self.high &= ~(np.uint32(1) << np.uint32((pos - 64)))

    def get_bit(self, pos):
        if pos < 64:
            return (self.low >> np.uint64(pos)) & np.uint64(1)
        else:
            return (self.high >> np.uint32((pos - 64))) & np.uint32(1)

    def __or__(self, other):
        return Bit90(self.low | other.low, self.high | other.high)

    def __and__(self, other):
        return Bit90(self.low & other.low, self.high & other.high)

    def __xor__(self, other):
        return Bit90(self.low ^ other.low, self.high ^ other.high)

    def __invert__(self):
        return Bit90(~self.low & ((np.uint64(1) << 64) - 1), ~self.high & ((np.uint32(1) << 26) - 1))

    def __repr__(self):
        top = (np.binary_repr(self.high, 26))
        bottom = (np.binary_repr(self.low, 64))
        combined = top + bottom
        rows = []
        for i in range(0, 90, 9):
            rows.append(combined[i:i + 9])
        formatted_output = '\n'.join(rows)
        return formatted_output
