from board import Board

class Game(object):
    """
    Models a single Game of the Amazons game, encapsulating the sequence of
    boards and moves that the game is passing or passed through.  Provides
    functionality for moving and undoing moves.
    """

    def __init__(self, width=10, height=10, white_amazons='a4, d1, g1, j4',
                 black_amazons='a7, d10, g10, j7', arrows='', to_move='white'):
        self._board = Board(width, height, white_amazons, black_amazons, arrows, to_move)
        self.moves = []
        self.winner = None
        self.ended_with_resign = False

    @property
    def board(self):
        return self._board

    @property
    def last_move(self):
        index = len(self.moves) - 1
        if index < 0:
            return None
        return self.moves[index]

    @property
    def is_over(self):
        return self.winner != None

    def undo(self, how_many=1):
        """Undo the last move, or the last specified number of moves."""
        for i in range(how_many):
            if len(self.moves) > 0:
                self._board.undo_move_in_place(self.moves.pop())

    def move(self, move):
        if self.is_over:
            raise InvalidMoveException('The game is over - no moves allowed')
        b = self._board
        if (move in ['resign', 'r', 'time_over']):
            self.winner = 'white' if b.to_move == 'black' else 'black'
            self.ended_with_resign = True
        else:
            self.moves.append(move)
            b.move_in_place(move)
            # If there are no moves left for the current player, the game is
            # over and the other player wins.
            if (len(b.get_valid_moves()) == 0):
                self.winner = 'white' if b.to_move == 'black' else 'black'

    def __str__(self):
        b = self._board
        game_status_str = str(b)
        return game_status_str