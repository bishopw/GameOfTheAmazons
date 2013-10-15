from board import Board

class Game(object):
    """
    Models a single Game of the Amazons game, encapsulating the sequence of
    boards and moves that the game is passing or passed through.  Provides
    functionality for moving and undoing moves.
    """

    def __init__(self, width=10, height=10, white_amazons='a4, d1, g1, j4',
                 black_amazons='a7, d10, g10, j7', arrows='', to_move='white'):
        self.boards = [Board(width, height, white_amazons,
                       black_amazons, arrows, to_move)]
        self.moves = []
        self.winner = None

    @property
    def board(self):
        return self.boards[len(self.boards) - 1]

    @property
    def is_over(self):
        return self.winner != None

    def move(self, move):
        if self.is_over:
            raise InvalidMoveException('The game is over - no moves allowed')
        b = self.board
        if (move in ['resign', 'r']):
            self.winner = 'white' if b.to_move == 'black' else 'black'
        else:
            b = b.move(move)
            self.boards.append(b)
            # If there are no moves left for the current player, the game is
            # over and the other player wins.
            if (len(b.get_valid_moves()) == 0):
                self.winner = 'white' if b.to_move == 'black' else 'black'

    def __str__(self):
        b = self.board
        game_status_str = str(b)
        return game_status_str