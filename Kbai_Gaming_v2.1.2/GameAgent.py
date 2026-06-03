from typing import Tuple

from Game import Game, Type
from Token import Token

TTT_LINES = [
    [(0,0),(0,1),(0,2)],
    [(1,0),(1,1),(1,2)],
    [(2,0),(2,1),(2,2)],
    [(0,0),(1,0),(2,0)],
    [(0,1),(1,1),(2,1)],
    [(0,2),(1,2),(2,2)],
    [(0,0),(1,1),(2,2)],
    [(0,2),(1,1),(2,0)],
]

TTT_CORNERS = [(0,0),(0,2),(2,0),(2,2)]


class GameAgent:
    def __init__(self, token: Token):
        self._token = token

    def token(self):
        return self._token

    def make_move(self, game: Game) -> Tuple[int, int] | int:
        if game.get_type() == Type.TIC_TAC_TOE:
            return self.ttt_move(game)
        else:
            return -1 

    def ttt_move(self, game: Game):
        board = game.get_board()
        token_opp = game.player2_token() if game.player1_token() == self._token else game.player1_token()

        #Win if possible
        move = GameAgent._find_if_winning_move_possible(board, self._token)
        if move:
            return move

        #Block opponent winning move
        move = GameAgent._find_if_winning_move_possible(board, token_opp)
        if move:
            return move

        # Board is empty start with a corner
        if (board == '').all():
            return TTT_CORNERS[0]

        # Take center if free 
        if board[1][1] == '':
            return (1, 1)

        #Take randomly a free corner. Well, half random.
        for r, c in TTT_CORNERS:
            if board[r][c] == '':
                return (r, c)

        return (-1, -1)

    def _find_if_winning_move_possible(board, token):
        val = token.value()
        for line in TTT_LINES:
            values = [board[r][c] for r, c in line]
            if values.count(val) == 2 and values.count('') == 1:
                empty_idx = values.index('')
                return line[empty_idx]
        return None
