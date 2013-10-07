import unittest

from board import Board

class BoardTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.default_board = Board()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_default_board(self):
        b = Board()
        self.assertTrue(isinstance(b, Board))
        self.assertTrue(b.width == 10)
        self.assertTrue(b.height == 10)
        self.assertTrue(len(b.white_amazons) == 4)
        self.assertTrue(len(b.black_amazons) == 4)
        self.assertTrue(len(b.arrows) == 0)

    def test_create_custom_boards(self):
        b = Board(100, 100)
        self.assertTrue(b.width == 100)
        self.assertTrue(b.height == 100)
        self.assertTrue(b.to_move == "white")
        b = Board(white_amazons = "a1, d1, g1, j1")
        self.assertTrue(b.width == 10)
        self.assertTrue(b.height == 10)
        self.assertTrue(b.to_move == "white")
        self.assertRaises(ValueError, Board, 10, 10, "invalid value")
        self.assertTrue(Board(to_move = Board.BLACK).to_move == "black")
        self.assertTrue(Board(to_move = 'black').to_move == "black")
        self.assertTrue(Board(to_move = 'b').to_move == "black")

    def test_square_lookup_with_index_operator(self):
        db = self.default_board
        self.assertTrue(db[0][0] == Board.EMPTY)
        self.assertTrue(db[0][3] == Board.WHITE)
        self.assertTrue(db[6][9] == Board.BLACK)
        with self.assertRaises(IndexError):
            x = db[0][-11]
        with self.assertRaises(IndexError):
            x = db[0][10]
        with self.assertRaises(IndexError):
            x = db[-11][0]
        with self.assertRaises(IndexError):
            x = db[10][0]

    def test_create_board_from_move(self):
        pass

    def test_move_enumeration(self):
        pass

    def test_territory_estimation(self):
        pass

if __name__ == "__main__":
    unittest.main() # run all tests