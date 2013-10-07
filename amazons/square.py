VALUE_ERROR_MSG = "A Square must be specified by a column and row, like a1"

class Square(object):
    """
    Represents a single square on a game board, providing functions for
    converting to and from standard board game square notation ('a4') to
    internal tuple representation ((0,3)).
    Accepts the following constructor forms:
    Square('a4')
    Square('4A')
    Square(0, 3)
    Square((0,3))
    Square()
    """

    @classmethod
    def parse_str(cls, s):
        s = s.lower().strip()
        s = ''.join(s.split()) # remove any internal spaces
        column = -1
        row = -1
        # split into alpha and numeric part, whether a1 or 1a
        for i in range(len(s) - 1):
            if (s[i].isalpha() and s[i+1].isdigit()):
                column = s[i]
                row = s[i+1:]
                break
            elif (s[i].isdigit() and s[i+1].isalpha()):
                row = s[:i+1]
                column = s[i+1]
                break
        if (row == -1 or column == -1):
            raise ValueError(VALUE_ERROR_MSG);
        return (ord(column) - 97, int(row) - 1)

    def __init__(self, *args):
        if (len(args) == 0):
            self.square = (0,0)
        elif (len(args) == 1):
            if (isinstance(args[0], Square)):
                # construct from other Square (copy constructor)
                self.square = (args[0][0], args[0][1])
            elif (type(args[0]) == tuple):
                # construct from tuple
                if (len(args[0]) != 2 or type(args[0][0]) != int or
                    type(args[0][1]) != int):
                    raise ValueError(("Squares can only be created from tuples "
                                      "of the form (int, int)"))
                if (args[0][0] < 0 or args[0][1] < 0):
                    raise ValueError("Square coordinates cannot be negative")
                self.square = args[0]
            elif (type(args[0]) == str):
                # construct from string
                self.square = Square.parse_str(args[0])
            else:
                raise ValueError("Could not create Square from %s" % 
                                 str(args[0]))
        elif (len(args) == 2):
            # construct from two int arguments
            if (type(args[0]) == int and type(args[1]) == int):
                if (args[0] < 0 or args[1] < 0):
                    raise ValueError("Square coordinates cannot be negative")
                self.square = (args[0], args[1])
            else:
                raise ValueError("Could not create Square with args %s, %s" %
                                 (str(args[0]), str(args[1])))
        else:
            raise ValueError("Too many arguments to Square()")

    def tuple(self):
        return self.square

    @property
    def column(self):
        return self.square[0]

    @property
    def row(self):
        return self.square[1]

    @property
    def x(self):
        return self.column

    @property
    def y(self):
        return self.row

    def __str__(self):
        return str(unichr(self.square[0] + 97)) + str(self.square[1] + 1)

    """
    Overload equality operators to compare Squares in tuple, string, or
    class form.
    """
    def __eq__(self, other):
        if (isinstance(other, Square)):
            pass # no conversion necessary for comparison
        elif (type(other) == str or type(other) == tuple):
            try: # try converting the string or tuple to a Square to compare
                other = Square(other)
            except Exception:
                return False
        else:
            return False
        return self[0] == other[0] and self[1] == other[1]

    def __ne__(self, other):
        return not (self == other)

    """Overload bracket operator."""
    def __getitem__(self, index):
        return self.square[index]