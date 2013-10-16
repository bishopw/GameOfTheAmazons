from random import randint

from move import Move
from board import Board
from game import Game
from invalid_move_error import InvalidMoveError
from player import Player
from board import WHITE,BLACK
from player import ResignGame,QuitGame

TITLE_ASCII = """                        ,---.
                        |  _.,---.,-.-.,---.
                        |   |,---|| | ||---'
                        `---'`---^` ' '`---'

                               of the

 @@@@@@   @@@@@@@@@@    @@@@@@   @@@@@@@@   @@@@@@   @@@  @@@   @@@@@@
@@@@@@@@  @@@@@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@ @@@  @@@@@@@
@@!  @@@  @@! @@! @@!  @@!  @@@       @@!  @@!  @@@  @@!@!@@@  !@@
!@!  @!@  !@! !@! !@!  !@!  @!@      !@!   !@!  @!@  !@!!@!@!  !@!
@!@!@!@!  @!! !!@ @!@  @!@!@!@!     @!!    @!@  !@!  @!@ !!@!  !!@@!!
!!!@!!!!  !@!   ! !@!  !!!@!!!!    !!!     !@!  !!!  !@!  !!!   !!@!!!
!!:  !!!  !!:     !!:  !!:  !!!   !!:      !!:  !!!  !!:  !!!       !:!
:!:  !:!  :!:     :!:  :!:  !:!  :!:       :!:  !:!  :!:  !:!      !:!
::   :::  :::     ::   ::   :::   :: ::::  ::::: ::   ::   ::  :::: ::
 :   : :   :      :     :   : :  : :: : :   : :  :   ::    :   :: : :
"""

class SimpleRunner(object):
    """
    A simple, command line game runner for Game of the Amazons.
    """

    def __init__(self, width=10, height=10, white_amazons='a4, d1, g1, j4',
                 black_amazons="a7, d10, g10, j7", arrows="", to_move='white'):
        self.game_settings = {
            'width': width,
            'height': height,
            'white_amazons': white_amazons,
            'black_amazons': black_amazons,
            'arrows': arrows,
            'to_move': to_move
        }
        self.white_player = Player(WHITE)
        self.black_player = Player(BLACK)
        self.clock = 'No Clock'

    def do_title_menu(self):
        print 'Please choose from the following options:'
        print '1) Set Player for White   (Current: ' + str(self.white_player) + ')'
        print '2) Set Player for Black   (Current: ' + str(self.black_player) + ')'
        print '3) Set Game Clock         (Current: ' + self.clock + ')'
        print '4) Reconfigure Board'
        print '5) Start Game'
        print 'q) Quit'
        print ''
        i = raw_input('> ').strip().lower()
        print ''
        if i == '1':
            self.do_set_player(0)
        elif i == '2':
            self.do_set_player(1)
        elif i == '3':
            self.do_set_clock()
        elif i == '4':
            self.do_reconfigure_board()
        elif i == '5':
            self.do_start_game()
        elif i in ['quit', 'q']:
            self.do_confirm_quit(self.do_title_menu)
        else:
            print "Sorry, I don't know how to do that."
            print ''
            self.do_title_menu()

    def do_set_player(self, player):
        player_str = 'White' if player == 0 else 'Black'
        current = self.white_player if player == 0 else self.black_player
        print 'Please choose a player for ' + player_str + ' (Current: ' + str(current) + '):'
        print '1) Local Human'
        print '2) Remote Human (via Network)'
        print '3) Computer AI'
        print ''
        i = raw_input('> ').strip().lower()
        print ''
        if i == '1':
            if player == 0:
                self.white_player = 'Local Human'
            else:
                self.black_player = 'Local Human'
            self.do_title_menu()
        elif i == '2':
            print "Sorry, that's not implemented yet."
            print ''
            self.do_set_player(player)
        elif i == '3':
            if player == 0:
                self.white_player = 'Computer AI'
            else:
                self.black_player = 'Computer AI'
            self.do_title_menu()
        else:
            print "Sorry, I don't know how to do that."
            print ''
            self.do_set_player(player)

    def do_set_clock(self):
        print "Sorry, that's not implemented yet."
        print ''
        self.do_title_menu()

    def do_reconfigure_board(self):
        print "Sorry, that's not implemented yet."
        print ''
        self.do_title_menu()

    def do_confirm_quit(self, func):
        print 'Quit?  Are you sure (y/n)?'
        print ''
        i = raw_input('> ').strip().lower()
        print ''
        if i == 'y':
            print 'Goodbye!'
            print ''
            # let execution fall through
        else:
            func() # cancel quit

    def do_start_game(self):
        s = self.game_settings
        self.game = Game(s['width'], s['height'], s['white_amazons'],
                         s['black_amazons'], s['arrows'], s['to_move'])
        
        while not self.game.is_over:
        	self.do_play_game()

    def do_play_game(self, print_board = True):
        g = self.game
        b = g.board
        curr_player = self.white_player if b.to_move == 'white' else self.black_player
        curr_player_name = str(b.to_move).capitalize()
        if str(curr_player) == 'Local Human':
            if print_board:
                print g
                print ''
            try:
                g.move(curr_player.next_move_txt(g))
            except QuitGame:
            	self.do_confirm_quit(self.do_play_game)
            except ResignGame:
                self.do_confirm_resign()

        elif curr_player == 'Computer AI':
            print curr_player_name + ' is thinking...'
            print ''
            move = self.get_ai_move()
            print curr_player_name + ' moves: ' + str(move) + '.'
            print ''
            g.move(move)
            if (g.is_over):
                self.do_finish_game()
            elif (self.white_player == self.black_player == 'Computer AI'):
                # Both players are AIs.
                # Give human spectators time to watch.
                print g
                print ''
                print 'Press any key to continue.'
                print ''
                i = raw_input()
                self.do_play_game(print_board = False)
            else:
                self.do_play_game()

    def get_ai_move(self):
        """Temporary stand-in for AI opponent.  Pick a random valid move."""
        valid_moves = self.game.board.get_valid_moves()
        return valid_moves[randint(0, len(valid_moves) - 1)]

    def do_confirm_resign(self):
        print self.game.board.to_move.capitalize() + ', really resign (y/n)?'
        print ''
        i = raw_input('> ').strip().lower()
        print ''
        if i == 'y':
            self.game.move('resign')
            self.do_finish_game()
        else:
            self.do_play_game(print_board = False)

    def do_finish_game(self):
        print self.game
        print ''
        print self.game.winner.capitalize() + ' won the game!'
        print ''
        print 'Press any key to start over.'
        print ''
        i = raw_input()
        self.do_title_menu()

    def run(self):
        print ''
        print 'Welcome to'
        print TITLE_ASCII
        print "an implementation of Walter Zamkauskas's Game of the Amazons"
        print 'by Bishop Wilkins and Justin Gregory'
        print 'for the System Development with Python UW course'
        print 'with Joseph Sheedy at EMC Isilon Storage Division, Q4 2013'
        print ''
        self.do_title_menu()

if __name__ == "__main__":
    SimpleRunner().run()