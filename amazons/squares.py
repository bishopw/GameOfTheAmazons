from square import Square

VALUE_ERROR_MSG = ("Squares should be specified as a string "
                   "like 'f6, j10, b4'")

class Squares(object):
    """
    An ordered list of squares on a game board, ordered from a1 in the lower left,
    left to right then low to high, to j10 in the upper right.  Internally
    represented as a list of Square objects.
    """

    def remove(self, sq):
        self.squares.remove(sq)
        if self.sort:
            self.squares.sort(key=lambda sq: ((sq[1] * self.row_width) + sq[0]))

    def append(self, sq):
        self.squares.append(sq)
        if self.sort:
            self.squares.sort(key=lambda sq: ((sq[1] * self.row_width) + sq[0]))

    def clear(self, sq):
        del self.squares[:]

    def __init__(self, *args, **kwargs):
        self.squares = []
        self.row_width = 1 # track the widest row we've seen for ordering

        # sort the squares unless instructed otherwise
        self.sort = kwargs.get('sort', True)

        if (len(args) == 1):
            if (type(args[0]) == str):
                # construct from a string of Square strings, like "a1, f6, j10"
                s = args[0].lower().strip()
                # strip out recognized delimiters
                s = s.replace(',', ' ')
                arr = s.split()
                for s in arr:
                    if (len(s.strip()) > 0):
                        sq = Square(s)
                        self.squares.append(sq)
                        if (sq[0] + 1) > self.row_width:
                            self.row_width = (sq[0] + 1)
            elif (type(args[0]) == list):
                # construct from a list of Square representations
                for i in args[0]:
                    sq = Square(i)
                    self.squares.append(sq)
                    if (sq[0] + 1) > self.row_width:
                        self.row_width = (sq[0] + 1)
            elif (isinstance(args[0], Squares)):
                # construct from another Squares object (copy constructor)
                for i in args[0].squares:
                    self.squares.append(Square(i))
                self.row_width = args[0].row_width
            else:
                raise ValueError(VALUE_ERROR_MSG)

        elif (len(args) > 1):
            # try to consider the args as a list of individual square specifiers
            for arg in args:
                sq = Square(arg)
                self.squares.append(sq)
                if (sq[0] + 1) > self.row_width:
                    self.row_width = (sq[0] + 1)

        # else there were no args: leave this as an empty squares list

        # sort the squares
        if self.sort:
            self.squares.sort(key=lambda sq: ((sq[1] * self.row_width) + sq[0]))

    def __str__(self):
        return ", ".join([str(Square(i)) for i in self.squares])

    """Overload bracket operator."""
    def __getitem__(self, index):
        return self.squares[index]

    def __len__(self):
        return len(self.squares)

    """Allow iterating over each Square in the list."""
    def __iter__(self):
        self._iter_pos = 0
        return self

    def next(self):
        if self._iter_pos >= (len(self.squares)):
            raise StopIteration
        else:
            self._iter_pos = self._iter_pos + 1
            return self.squares[self._iter_pos - 1]

    """
    Allow equality testing using strings, tuples, lists, or other strings
    objects.
    """
    def __eq__(self, other):
        if (not isinstance(other, Squares)):
            try:
                other = Squares(other)
            except Exception:
                return False
        if (len(self) != len(other)):
            return False
        for i in range(len(self.squares)):
            if (self.squares[i] != other.squares[i]):
                return False
        return True

    def __ne__(self, other):
        return not (self == other)