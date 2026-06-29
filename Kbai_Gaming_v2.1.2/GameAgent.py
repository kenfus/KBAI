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
        elif game.get_type() in [Type.CONNECT_4_BASIC, Type.CONNECT_4_EXTENDED, Type.CONNECT_4_MULTIPLAYER, Type.CONNECT_4_HIDDEN_MULTIPLAYER]:
            return self.cf_move(game)
        else:
            return -1 



    def cf_move(self, game: Game):
        board = game.get_board()


        token_opps = [game.player1_token() ,game.player2_token(), game.player3_token()]
        token_opps.remove(self._token)
        token_opps = [t for t in token_opps if t is not None]

        how_many_to_win = game.number_of_seq_tokens_needed()

        rows, cols = board.shape
        #Win if possible
        move = GameAgent._find_if_winning_move_c4_possible(board, self._token, how_many_to_win)
        if move is not None:
            return move

        #Block opponent winning move
        for token_opp in token_opps:
            move = GameAgent._find_if_winning_move_c4_possible(board, token_opp, how_many_to_win)
            if move is not None:
                return move

        # Board is empty start in the center
        if (board == '').all():
            return int(cols // 2)

        #Take first available free space column from the middle..
        columns_from_middle = list(range(cols // 2, cols)) + list(range(cols // 2 - 1, -1, -1))
        for c in columns_from_middle:
            if GameAgent._c4_column_has_enough_open_spaces(board, c, how_many_to_win):
                return c

        # Else random 
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
    

    
    def _c4_position_is_playable(board, row, col):
        return row == board.shape[0] - 1 or board[row + 1][col] != ''

    def _c4_column_has_space(board, col):
        return '' in board[:, col]

    def _c4_column_has_enough_open_spaces(board, col, needed):
        return list(board[:, col]).count('') >= needed
    


    def _find_if_winning_move_c4_possible(board, token, n):
        val = token.value()
        rows, cols = board.shape

        # Check horizontal
        for r in range(rows):
            for c in range(cols - n + 1):
                window = board[r, c:c+n]
                if list(window).count(val) == n - 1 and list(window).count('') == 1:
                    empty_idx = list(window).index('')
                    move_col = c + empty_idx
                    if GameAgent._c4_position_is_playable(board, r, move_col):
                        return move_col
                

        # Check vertical
        for c in range(cols):
            for r in range(rows - n + 1):
                window = board[r:r+n, c]
                if list(window).count(val) == n - 1 and list(window).count('') == 1:
                    empty_idx = list(window).index('')
                    move_row = r + empty_idx
                    if GameAgent._c4_position_is_playable(board, move_row, c):
                        return c


        # Check diagonal (bottom-left to top-right) 
        for r in range(n - 1, rows):
            for c in range(cols - n + 1):
                window = [board[r-i][c+i] for i in range(n)]
                if window.count(val) == n - 1 and window.count('') == 1:
                    empty_idx = window.index('')
                    move_row = r - empty_idx
                    move_col = c + empty_idx
                    if GameAgent._c4_position_is_playable(board, move_row, move_col):
                        return move_col
                


        # Check diagonal  (top-left to bottom-right)
        for r in range(rows - n + 1):
            for c in range(cols - n + 1):
                window = [board[r+i][c+i] for i in range(n)]
                if window.count(val) == n - 1 and window.count('') == 1:
                    empty_idx = window.index('')
                    move_row = r + empty_idx
                    move_col = c + empty_idx
                    if GameAgent._c4_position_is_playable(board, move_row, move_col):
                        return move_col
                    

        return None


    def _find_if_winning_move_possible(board, token):
        val = token.value()
        for line in TTT_LINES:
            values = [board[r][c] for r, c in line]
            if values.count(val) == 2 and values.count('') == 1:
                empty_idx = values.index('')
                return line[empty_idx]
        return None
