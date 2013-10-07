from memoize import memoized

from square import Square
from squares import Squares
from move import Move
from invalid_move_error import InvalidMoveError

# Board index constants.
EMPTY = 0
WHITE = 1
BLACK = 2
ARROW = 3

SQUARE_OCCUPANT_NAMES = {
    EMPTY: "empty",
    WHITE: "white amazon",
    BLACK: "black amazon",
    ARROW: "arrow"
}

SQUARE_OCCUPANT_SYMBOLS = {
    EMPTY: '.',
    WHITE: 'W',
    BLACK: 'B',
    ARROW: 'x'
}

DIRECTIONS = [
    (0, 1),   # north
    (1, 1),   # northeast
    (1, 0),   # east
    (1, -1),  # southeast
    (0, -1),  # south
    (-1, -1), # southwest
    (-1, 0),  # west
    (-1, 1)   # northwest
]

class Board(object):
    """
    A Game of the Amazons board.  Encapsulates the state of the board at a
    specific turn during a game, and functionality for enumerating legal moves,
    calculating territory, and such.
    """

    @classmethod
    def column_label(cls, col):
        """Returns a letter representing the column number specified by col."""
        return unichr(col + 97)

    def __init__(self, width=10, height=10, white_amazons="a4, d1, g1, j4",
                 black_amazons="a7, d10, g10, j7", arrows="", to_move=WHITE,
                 prev_board=None, move=None):
        if (prev_board == None and move == None):
            # Regular constructor.
            self.width = width
            self.height = height
            self.white_amazons = Squares(white_amazons)
            self.black_amazons = Squares(black_amazons)
            self.arrows = Squares(arrows)
            self.to_move = to_move

        elif isinstance(prev_board, Board) and move == None:
            # Copy constructor.
            self.width = prev_board.width
            self.height = prev_board.height
            self.white_amazons = Squares(prev_board.white_amazons)
            self.black_amazons = Squares(prev_board.black_amazons)
            self.arrows = Squares(prev_board.arrows)
            self.to_move = prev_board.to_move

        elif isinstance(prev_board, Board) and isinstance(move, Move):
            # Move constructor - construct a board like prev_board but with
            # the specified move applied.
            prev_board.check_is_move_valid(move);

            self.width = prev_board.width
            self.height = prev_board.height

            # Move the amazon.
            start = move[0]
            end = move[1]
            arrow = move[2]
            move_us = (prev_board.white_amazons if prev_board.to_move == 'white'
                       else prev_board.black_amazons)
            new_positions = [end]
            for sq in move_us:
                if sq != start:
                    new_positions.append(sq)
            if prev_board.to_move == 'white':
                self.white_amazons = Squares(new_positions)
                self.black_amazons = Squares(prev_board.black_amazons)
            else:
                self.white_amazons = Squares(prev_board.white_amazons)
                self.black_amazons = Squares(new_positions)

            # Shoot the arrow.
            self.arrows = Squares([sq for sq in prev_board.arrows] + [arrow])

            # Flip whose turn it is.
            self._to_move = WHITE if prev_board.to_move == 'black' else BLACK

        else:
            raise ValueError('Invalid Board constructor arguments')


    @property
    def to_move(self):
        return "white" if (self._to_move == WHITE) else "black"

    @to_move.setter
    def to_move(self, value):
        if hasattr(self, '_to_move'):
            raise AttributeError("to_move can't be changed")
        if (type(value) == int and value == WHITE or value == BLACK):
            self._to_move = value
        elif (type(value) == str):
            value = value.lower()
            self._to_move = WHITE if value in ['white', 'w'] else BLACK
        else:
            raise AttribueError(("to_move should be Board.WHITE, Board.BLACK, "
                                 "'white', 'black', 'w', or 'b'"))

    @property
    def current_amazons(self):
        """
        Get the Squares list representing the amazons whose turn it is to move.
        """
        return (self.white_amazons if self.to_move == "white" 
                else self.black_amazons)

    @property
    def opponent_amazons(self):
        """
        Get the amazons that are not to move this turn.
        """
        return (self.white_amazons if self.to_move == "black"
                else self.black_amazons)

    @memoized
    def get_board(self):
        """
        Returns a two-dimensional list such that get_board()[column][row] is
        the board index constant (Board.EMPTY, Board.WHITE, Board.BLACK, or
        Board.ARROW) at the given row and column.
        """
        # Initialize empty board.
        columns = [[EMPTY for r in range(self.height)]
                   for c in range(self.width)]

        # Place amazons and arrows, raising an error if there is any collision.
        for amz in self.white_amazons:
            occupant = columns[amz[0]][amz[1]]
            if (occupant != EMPTY):
                raise ValueError(("Board position %s can't be occupied by "
                                  "both %s and %s") % (str(amz),
                                  SQUARE_OCCUPANT_NAMES[occupant],
                                  SQUARE_OCCUPANT_NAMES[WHITE]))
            columns[amz[0]][amz[1]] = WHITE
        for amz in self.black_amazons:
            occupant = columns[amz[0]][amz[1]]
            if (occupant != EMPTY):
                raise ValueError(("Board position %s can't be occupied by "
                                  "both %s and %s") % (str(amz),
                                  SQUARE_OCCUPANT_NAMES[occupant],
                                  SQUARE_OCCUPANT_NAMES[BLACK]))
            columns[amz[0]][amz[1]] = BLACK
        for arr in self.arrows:
            occupant = columns[arr[0]][arr[1]]
            if (occupant != EMPTY):
                raise ValueError(("Board position %s can't be occupied by "
                                  "both %s and %s") % (str(arr),
                                  SQUARE_OCCUPANT_NAMES[occupant],
                                  SQUARE_OCCUPANT_NAMES[ARROW]))
            columns[arr[0]][arr[1]] = ARROW
        return columns

    def get_valid_moves(self):
        """
        Memoizes and/or returns the full list generated by the 
        enumerate_valid_moves generator.  I could have used the @memoize
        decorator but we might want an explicit reference to the cached moves to
        query in other methods to see if we need to generate them or not.
        """
        if not hasattr(self, '_valid_moves'):
            self._valid_moves = [mv for mv in self.enumerate_valid_moves(self)]
        return self._valid_moves

    class enumerate_valid_moves(object):
        """Generator for a list of all valid moves on this board."""

        def __init__(self, board):
            self.board = board

            # Index in white or black amazons list of amazon whose moves are
            # currently being enumerated.
            self.curr_amazon = 0

            # Current direction of moves being enumerated, from 0 = north to
            # 7 = northwest
            self.curr_amazon_dir = 0

            # Current distance of move being enumerated in squares from amazon.
            self.curr_amazon_dist = 1

            # Current direction and distance of arrow shot being enumerated.
            self.curr_arrow_dir = 0
            self.curr_arrow_dist = 1

        def __iter__(self):
            return self

        # Python 3 compatibility.
        def __next__(self):
            return self.next()

        def next(self):
            # Iterate through each amazon -> direction -> distance ->
            # arrow direction -> arrow distance.  (That order will appear in
            # reverse in this function because we need to check the cases from
            # the inmost to the outmost.)
            mv = None
            b = self.board
            if len(b.current_amazons) < 1:
                raise StopIteration() # Special case: No amazons on the board.
            while (True):
                amz = b.current_amazons[self.curr_amazon]
                amz_dir = DIRECTIONS[self.curr_amazon_dir]
                amz_dist = self.curr_amazon_dist
                arr_dir = DIRECTIONS[self.curr_arrow_dir]
                arr_dist = self.curr_arrow_dist

                amz_target = None
                try:
                    amz_target = Square(amz.x + (amz_dir[0] * amz_dist),
                                        amz.y + (amz_dir[1] * amz_dist))
                    if b[amz_target.x][amz_target.y] != EMPTY:
                        amz_target = None
                except:
                    amz_target = None

                next_amz_target = None
                try:
                    next_amz_target = Square(amz.x + (amz_dir[0] * (amz_dist + 1)),
                                             amz.y + (amz_dir[1] * (amz_dist + 1)))
                    if b[next_amz_target.x][next_amz_target.y] != EMPTY:
                        next_amz_target = None
                except:
                    next_amz_target = None

                arr = None
                try:
                    arr = Square(amz_target.x + (arr_dir[0] * arr_dist),
                                 amz_target.y + (arr_dir[1] * arr_dist))
                    if b[arr.x][arr.y] != EMPTY and arr != amz:
                        arr = None
                except:
                    arr = None

                # Is the path clear from the target square to the arrow square?
                # If so, we found a valid move:
                if (amz_target != None and arr != None and
                    b.is_path_clear(amz_target, arr, ignore=amz)):
                    # Increment the arrow distance and return this move.
                    self.curr_arrow_dist = self.curr_arrow_dist + 1
                    return Move(amz, amz_target, arr)
                # If not, this arrow distance is done.
                # Check the next arrow direction - is there another?
                elif self.curr_arrow_dir < 7:
                    # If so, reset arrow distance.
                    self.curr_arrow_dist = 1
                    # Continue with the next arrow direction.
                    self.curr_arrow_dir = self.curr_arrow_dir + 1
                    continue
                # If not, this target square is done.
                # Is the path clear from the amazon to the next target square?
                elif (next_amz_target != None and
                      b.is_path_clear(amz, next_amz_target)):
                    # If so reset arrow distance and direction.
                    self.curr_arrow_dist = 1
                    self.curr_arrow_dir = 0
                    # Continue with the next target square.
                    self.curr_amazon_dist = self.curr_amazon_dist + 1
                    continue
                # If not, this amazon direction is done.
                # Check the next amazon direction - is there another?
                elif self.curr_amazon_dir < 7:
                    # If so, reset arrow distance, direction, and amazon dist.
                    self.curr_arrow_dist = 1
                    self.curr_arrow_dir = 0
                    self.curr_amazon_dist = 1
                    # Continue with the next amazon direction.
                    self.curr_amazon_dir = self.curr_amazon_dir + 1
                    continue
                # If not, this amazon is done.
                # Is there another amazon?
                elif self.curr_amazon < (len(b.current_amazons) - 1):
                    # If so, reset arrow dist and dir, and amazon dist and dir.
                    self.curr_arrow_dist = 1
                    self.curr_arrow_dir = 0
                    self.curr_amazon_dist = 1
                    self.curr_amazon_dir = 0
                    # Continue with the next amazon.
                    self.curr_amazon = self.curr_amazon + 1
                    continue
                else:
                    # If not, we've enumerated all moves.
                    # Turn off the generator.
                    raise StopIteration()

    def __getitem__(self, index):
        return self.get_board()[index]

    def __str__(self):
        """
        Return a simple ascii-text representation of the board.  Includes
        newlines and may not be suitable for printing in short string output.
        """
        str_list = []
        col_labels = '   ' + ''.join(['%3s' % Board.column_label(i)
                                      for i in range(self.width)]) + '\n'

        # board rows
        for r in reversed(range(self.height)):
            # leftside row label
            str_list.append('%3s' % (r + 1))
            for c in range(self.width):
                str_list.append('%3s' % SQUARE_OCCUPANT_SYMBOLS[self[c][r]])
            str_list.append('\n')

        # bottom column labels
        str_list.append(col_labels)

        return ''.join(str_list)

    def is_path_clear(self, start, end, ignore = None):
        """
        Returns True if there is a straight line path along one of the eight
        cardinal directions from start to end squares, and if it is not blocked
        by any arrow or amazon (not including one that may be at start).
        Returns False otherwise.
        """
        cur = start

        # Figure out which direction to move.
        dir = {'x': 0, 'y': 0}
        if cur.x < end.x:
            dir['x'] = 1
        elif cur.x == end.x:
            dir['x'] = 0
        else: # cur.x > end.x
            dir['x'] = -1
        if cur.y < end.y:
            dir['y'] = 1
        elif cur.y == end.y:
            dir['y'] = 0
        else: # cur.y > end.y
            dir['y'] = -1
        if dir['x'] == 0 and dir['y'] == 0:
            return False

        # Attempt to walk the path.
        while (cur != end):
            cur = Square(cur.x + dir['x'], cur.y + dir['y'])
            if cur == ignore:
                continue
            try:
                occupant = self[cur.x][cur.y]
                if (occupant != EMPTY):
                    return False
            except IndexError:
                # We must have walked off the board due to the target not being
                # in a straight line from the starting square.
                return False

        return True

    def check_is_move_valid(self, move):
        """
        Returns true if the specified move is valid on this board, otherwise
        throws an InvalidMoveError containing the problem with the move.
        """
        move = Move(move)
        frm = move[0]
        to = move[1]
        arrow = move[2]

        # Make sure all the specified squares are on the board.
        for sq in move:
            if (sq.x < 0 or sq.x >= self.width or
                sq.y < 0 or sq.y >= self.height):
                raise InvalidMoveError(str(sq) + ' is not on the board')

        # Make sure there's an amazon of the right color at the specified
        # from location.
        amz = self[frm[0]][frm[1]]
        if amz != self._to_move:
            raise InvalidMoveError('No ' + self.to_move +
                                   ' amazon at ' + str(frm))

        # Make sure the target is different from the start location
        if (frm == to):
            raise InvalidMoveError('You have to move your amazon each turn')

        # Make sure the target location is along a clear path from the amazon
        # to move.
        if not self.is_path_clear(frm, to):
            raise InvalidMoveError("There's no path from " + str(frm) +
                                   ' to ' + str(to))

        # Make sure the arrow location is different than the move target
        if (to == arrow):
            raise InvalidMoveError(("You can't shoot an arrow onto the same "
                                    "square you are moving to"))

        # Make sure the arrow location is along a clear path from the target
        # location.
        if not self.is_path_clear(to, arrow, ignore=frm):
            raise InvalidMoveError("There's no path from " + str(to) +
                                   ' to ' + str(arrow))

    def move(self, move):
        """
        Makes the specified move, returning a new Board representing the
        game state after the move is made.  The original Board is not changed.
        If the specified move is not legal for this board, an InvalidMoveError
        is raised.
        """
        return Board(prev_board=self, move=move)

# Export board index constants as properties of the Board class.
Board.EMPTY = EMPTY
Board.WHITE = WHITE
Board.BLACK = BLACK
Board.ARROW = ARROW
Board.SQUARE_OCCUPANT_NAMES = SQUARE_OCCUPANT_NAMES