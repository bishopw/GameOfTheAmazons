import unittest

from square import Square
from squares import Squares

class SquaresTest(unittest.TestCase):

    def test_create_default_squares(self):
        sqs = Squares()
        self.assertTrue(len(sqs) == 0)

    def test_create_squares_with_strings(self):
        sqs = Squares('a1, f6, j10')
        self.assertTrue(len(sqs) == 3)
        self.assertTrue(sqs[0] == 'a1')
        self.assertTrue(sqs[1] == (5, 5))
        self.assertTrue(sqs[2] == (9, 9))
        sqs2 = Squares(['a1', 'f6', 'j10'])
        self.assertTrue(len(sqs2) == 3)
        self.assertTrue(sqs2[0] == 'a1')
        self.assertTrue(sqs2[1] == (5, 5))
        self.assertTrue(sqs2[2] == (9, 9))
        self.assertTrue(sqs == sqs2)
        sqs3 = Squares('a1', 'f6', 'j10')
        self.assertTrue(len(sqs3) == 3)
        self.assertTrue(sqs3[0] == 'a1')
        self.assertTrue(sqs3[1] == (5, 5))
        self.assertTrue(sqs3[2] == (9, 9))
        self.assertTrue(sqs == sqs3)
        self.assertTrue(Squares('a1, f6, j10') == Squares('a1 j10     f6'))
        sqs = Squares('')
        self.assertTrue(isinstance(sqs, Squares))
        self.assertTrue(len(sqs) == 0)
        self.assertTrue(sqs == [])

    def test_create_squares_with_tuples(self):
        sqs = Squares([(0, 0), (10, 4), (6, 11), (2, 2)])
        self.assertTrue(len(sqs) == 4)
        self.assertTrue(sqs == 'a1, c3, g12, k5')
        self.assertTrue(sqs[2] == 'k5')
        sqs2 = Squares((0, 0), (10, 4), (6, 11), (2, 2))
        self.assertTrue(len(sqs2) == 4)
        self.assertTrue(sqs2 == 'a1, c3, g12, k5')
        self.assertTrue(sqs2[2] == 'k5')
        self.assertTrue(sqs == sqs2)

    def test_create_squares_with_squares(self):
        sqs = Squares(Square('d8'), Square(9, 2), Square((9, 9)))
        self.assertTrue(len(sqs) == 3)
        self.assertTrue(sqs == 'j3, d8, j10')
        sqs2 = Squares([Square('d8'), Square(9, 2), Square((9, 9))])
        self.assertTrue(len(sqs2) == 3)
        self.assertTrue(sqs2 == 'j3, d8, j10')
        self.assertTrue(sqs == sqs2)

    def test_create_squares_with_mixture(self):
        sqs = Squares('100x', (8, 8), Square('b2'))
        self.assertTrue(len(sqs) == 3)
        self.assertTrue(sqs == 'b2 i9 100x')
        sqs2 = Squares(['100x', (8, 8), Square('b2')])
        self.assertTrue(len(sqs2) == 3)
        self.assertTrue(sqs2 == 'b2 i9 100x')
        self.assertTrue(sqs == sqs2)

    def test_create_squares_with_copy_constructor(self):
        sqs = Squares('d6, e2, f5, f10, j1')
        sqs2 = Squares(sqs)
        self.assertTrue(isinstance(sqs2, Squares))
        self.assertTrue(sqs2 == 'j1, e2, f5, d6, f10')
        self.assertTrue(sqs == sqs2)
        self.assertFalse(sqs.squares is sqs2.squares) # are they really copies?

    def test_invalid_squares_creates(self):
        self.assertRaises(ValueError, Squares, 'asdfasdf')
        self.assertRaises(ValueError, Squares, [()])
        self.assertRaises(ValueError, Squares, (5, 6))
        self.assertRaises(ValueError, Squares, [(0, 1), (-3, 4), (6, 8)])
        self.assertRaises(ValueError, Squares, '100x', (8, 8), 'g')
        self.assertRaises(ValueError, Squares, '4d', '6c', '77')
        self.assertRaises(ValueError, Squares, None)

    def test_squares_ordering(self):
        sqs = Squares('c5, c10, a2, j2, a1')
        # constructor accepts squares in any order to create the ordered list
        self.assertTrue(sqs == 'c5, c10, a2, j2, a1')
        # __str__() returns a string representation in strict order
        self.assertTrue(str(sqs) != 'c5, c10, a2, j2, a1')
        self.assertTrue(str(sqs) == 'a1, a2, j2, c5, c10')

    def test_squares_equality_operators(self):
        self.assertTrue(Squares() == Squares([]))
        self.assertTrue(Squares() != Squares('h4'))
        self.assertTrue(Squares('d12') != Squares('h4'))
        self.assertTrue(Squares('a2 c12 l18') ==
                        Squares((0, 1), (11, 17), (2, 11)))
        self.assertTrue(Squares((0, 0), (1, 1), (2, 2)) == 'a1, b2, c3')
        self.assertTrue('a1, b2, c3' == Squares((0, 0), (1, 1), (2, 2)))
        self.assertTrue(Squares('a1, b2, c3') == 'a1, b2, c3')
        self.assertTrue(Squares('a1, b2, c3') == 'c3, b2, a1')
        self.assertTrue(Squares('a1, b2, c3') != 'a1, b2, c4')
        self.assertTrue(Squares('a1, b2, c3') == ['a1', 'b2', 'c3'])
        self.assertTrue(Squares('a1, b2, c3') != ['b1', 'b2', 'c3'])
        self.assertFalse(Squares('a1, b2, c3') == [(-1, 5)])

    def test_squares_index_operator(self):
        sqs = Squares('b4, d7, j1')
        self.assertTrue(sqs[0] == 'j1')
        self.assertTrue(sqs[1] == (1, 3))
        self.assertTrue(sqs[2] == 'd7')
        with self.assertRaises(IndexError):
            sq = sqs[3]

    def test_squares_iteration(self):
        sqs = Squares('d7, g3, j10, a2')
        results = []
        for sq in sqs:
            results.append(sq)
        self.assertTrue(len(results) == 4)
        self.assertTrue(results[0] == 'a2')
        self.assertTrue(results[1] == 'g3')
        self.assertTrue(results[2] == 'd7')
        self.assertTrue(results[3] == 'j10')
        self.assertTrue('d7' in sqs)
        self.assertTrue((9, 9) in sqs)

if __name__ == "__main__":
    unittest.main() # run all tests