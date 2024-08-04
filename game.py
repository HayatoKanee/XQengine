import utils
from board import Board
from utils import *


class Game:
    def __init__(self):
        self.board = Board()

    def run(self, fen=None):
        if fen:
            self.board.load_fen(fen)
        else:
            self.board.reset()
        while not self.board.end:
            print(self.board)
            h_input = input("Enter your move: ")
            if not validate_human_input(h_input):
                print("Example:a0a9")
                continue
            action = (convert_rank_file_to_index(h_input[0:2]), convert_rank_file_to_index(h_input[2:4]))
            self.board.generate_legal_actions()
            if not self.board.check_action(action):
                print("Invalid move")
                continue
            self.board.generate_next_state(action)
        print(f"{get_opponent_colour(self.board.turn)} wins")


game = Game()
game.run()
