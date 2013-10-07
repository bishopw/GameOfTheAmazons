import unittest

from square import Square

class SquareTest(unittest.TestCase):

    def test_create_default_square(self):
        sq = Square()
        self.assertTrue(sq.tuple() == (0,0))
        self.assertTrue(str(sq) == 'a1')

    def test_create_square_with_string(self):
        sq = Square('a1')
        self.assertTrue(sq.tuple() == (0,0))
        self.assertTrue(str(sq) == 'a1')
        sq = Square('1A')
        self.assertTrue(sq.tuple() == (0,0))
        self.assertTrue(str(sq) == 'a1')
        self.assertTrue(Square('f6').tuple() == (5,5))
        self.assertTrue(str(Square('f6')) == 'f6')
        self.assertTrue(Square('10 J').tuple() == (9,9))
        self.assertTrue(str(Square('10 J')) == 'j10')
        sq = Square('z999999')
        self.assertTrue(sq.tuple() == (25,999998))
        self.assertTrue(str(sq) == 'z999999')

    def test_create_square_with_tuple(self):
        sq = Square((3, 3))
        self.assertTrue(sq.tuple() == (3,3))
        self.assertTrue(str(sq) == 'd4')
        sq = Square((999999, 999999))
        self.assertTrue(sq.tuple() == (999999, 999999))
        self.assertRaises(ValueError, Square, (-4, 5))
        self.assertRaises(ValueError, Square, (4, -5))

    def test_create_square_with_multiple_args(self):
        sq = Square(4, 5)
        self.assertTrue(sq.tuple() == (4, 5))
        self.assertTrue(str(sq) == 'e6')

    def test_create_square_with_copy_constructor(self):
        sq = Square('e7')
        sq2 = Square(sq)
        self.assertTrue(sq2.tuple() == (4, 6))
        self.assertTrue(str(sq2) == 'e7')
        self.assertTrue(sq2 == sq)
        self.assertFalse(sq.square is sq2.square) # are they really copies?

    def test_square_index_operator(self):
        sq = Square('i7')
        self.assertTrue(sq[0] == 8)
        self.assertTrue(sq[1] == 6)
        with self.assertRaises(IndexError):
            i = sq[2]

    def test_square_equality_operators(self):
        sq = Square('b3')
        sq2 = Square(sq)
        sq3 = Square('7h')
        self.assertEqual(sq, sq2)
        self.assertTrue(sq == (1, 2))
        self.assertFalse(sq != (1, 2))
        self.assertTrue(sq == '3B')
        self.assertFalse(sq != '3B')
        self.assertTrue(sq != sq3)
        self.assertFalse(sq == sq3)
        self.assertFalse(sq != sq2)
        self.assertFalse(sq == None)
        self.assertTrue(sq != 'some random string')
        self.assertFalse(sq == (1, 2, 3, 4, 5))

    def test_invalid_square_creates(self):
        self.assertRaises(ValueError, Square, 'j,10')
        self.assertRaises(ValueError, Square, '10,j')
        self.assertRaises(ValueError, Square, 'j')
        self.assertRaises(ValueError, Square, '10')
        self.assertRaises(ValueError, Square, 'j10j')
        self.assertRaises(ValueError, Square, '')
        self.assertRaises(ValueError, Square, 'j-10')
        self.assertRaises(ValueError, Square, (1, 2, 3))
        self.assertRaises(ValueError, Square, 1, 2, 3)
        self.assertRaises(ValueError, Square, 'a', 1)
        self.assertRaises(ValueError, Square, 0, -1)
        self.assertRaises(ValueError, Square, -5, -5)
        self.assertRaises(ValueError, Square, 0, -9)
        self.assertRaises(ValueError, Square, (-5, -5))
        self.assertRaises(ValueError, Square, None)

if __name__ == "__main__":
    unittest.main() # run all tests