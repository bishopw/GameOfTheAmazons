from squares import Squares
from invalid_move_error import InvalidMoveError

class Move(Squares):
    """
    Represents a single move in a game of Amazons. Just a Squares that's not
    ordered by default to preserve the intended order of the move squares.
    """

    def __init__(self, *args):
        super(Move, self).__init__(*args, sort=False)

        if len(self) != 3:
            raise InvalidMoveError(('A move must specify three squares: from, '
                                    'to, and arrow locations'))