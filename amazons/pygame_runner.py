import os, sys

import pygame
from pygame.locals import *
from pgu import gui

from square import Square
from move import Move
from board import Board,BLACK,WHITE
from game import Game
from player import Player,NetworkPlayer,GameHostPlayer
from ai_player import AIPlayer
from clock import Clock
import socket

# Useful constants.
SQUARE_PX = 60 # Size of a board square in pixels.
BORDER_PX = 30 # Size of the borders of the board in pixels.

TERRITORY_MARK_NONE = 0
TERRITORY_MARK_SECURED = 1
TERRITORY_MARK_ESTIMATED = 2

class PygameRunner(object):
    """
    A pygame-based GUI and game controller for Game of the Amazons.

    Pygame app outline originally based on the Pygame Cheat Sheet:
    http://inventwithpython.com/pygamecheatsheet.png
    """

    # Different phases the game app can be in.
    PHASE_TITLE = 0
    PHASE_TRANSITION = 1
    PHASE_WAIT_FOR_AI = 2
    PHASE_WAIT_FOR_REMOTE = 3
    PHASE_PICK_AMAZON = 4
    PHASE_PLACE_AMAZON = 5
    PHASE_SHOOT_ARROW = 6
    PHASE_GAME_OVER = 7
    PHASE_TRANSITION_BACK = 8

    def __init__(self, width=10, height=10, white_amazons='a4, d1, g1, j4',
                 black_amazons="a7, d10, g10, j7", arrows="", to_move='white'):
        """Initialize the basic settings for this game."""
        self.game_settings = {
            'width': width,
            'height': height,
            'white_amazons': white_amazons,
            'black_amazons': black_amazons,
            'arrows': arrows,
            'to_move': to_move
        }
        self.app_settings = {
            'w_player': 'human',
            'w_difficulty': 5,
            'w_use_fixed_time': False,
            'w_minutes': 20,
            'w_seconds': 0,
            'w_use_byoyomi': False,
            'w_byoyomi_periods': 5,
            'w_byoyomi_seconds': 30,
            'b_player': 'ai',
            'b_difficulty': 5,
            'b_use_fixed_time': False,
            'b_minutes': 20,
            'b_seconds': 0,
            'b_use_byoyomi': False,
            'b_byoyomi_periods': 5,
            'b_byoyomi_seconds': 30,
            'territory_marking': TERRITORY_MARK_NONE,
            'show_ai_details': False
        }
        self.white_player = Player(WHITE)
        self.black_player = Player(BLACK)

        s = self.game_settings
        self.game = Game(s['width'], s['height'], s['white_amazons'],
                         s['black_amazons'], s['arrows'], s['to_move'])

        self.w_clock = None
        self.b_clock = None

        self.phase = self.PHASE_TITLE

        self.amazon_in_hand = None # Amazon currently being held by player.
        self.amazon_target = None  # Chosen target to move the amazon to.
        self.is_dragging = False   # Is the player mouse-dragging an amazon?


    # GAME AND APP CONTROL ####################################################
    def run(self):
        """
        Start up the pygame timing and video systems, run the game, then quit
        once the player is done.
        """
        pygame.init()
        self.fpsClock = pygame.time.Clock()

        # Prepare the main window surface that graphics will be rendered to.
        # Make it 90% of the desktop height and width.
        info = pygame.display.Info()
        self.screen_w = int(info.current_w * .9)
        self.screen_h = int(info.current_h * .9)
        self.window = pygame.display.set_mode((self.screen_w, self.screen_h))

        # Make sure we are in the module directory with the resources folder.
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Load resources.
        self.surfaces = {
            'app_icon': pygame.image.load('res/app_icon.png'),
            'arrow_cursor': pygame.image.load('res/arrow_cursor.png'),
            'arrow': pygame.image.load('res/arrow.png'),
            'black_cursor': pygame.image.load('res/black_cursor.png'),
            'black_territory': pygame.image.load('res/black_territory.png'),
            'black_wins': pygame.image.load('res/black_wins.png'),
            'black': pygame.image.load('res/black.png'),
            'board': pygame.image.load('res/board.png'),
            'circle': pygame.image.load('res/circle.png'),
            'cursor': pygame.image.load('res/cursor.png'),
            'hazy_black': pygame.image.load('res/hazy_black.png'),
            'hazy_white': pygame.image.load('res/hazy_white.png'),
            'last_move': pygame.image.load('res/last_move.png'),
            'stone': pygame.image.load('res/stone.png'),
            'title': pygame.image.load('res/title.png'),
            'white_cursor': pygame.image.load('res/white_cursor.png'),
            'white_territory': pygame.image.load('res/white_territory.png'),
            'white_wins': pygame.image.load('res/white_wins.png'),
            'white': pygame.image.load('res/white.png'),
            'x': pygame.image.load('res/x.png')
        }
        self.colors = {
            'red': pygame.Color(255, 0, 0),
            'green': pygame.Color(0, 255, 0),
            'blue': pygame.Color(0, 0, 255),
            'black': pygame.Color(0, 0, 0),
            'white': pygame.Color(255, 255, 255)
        }
        self.fonts = {
            'freesansbold': pygame.font.Font('freesansbold.ttf', 32),
            'comicsansms': pygame.font.Font('res/comicsansms.ttf', 24)
        }
        self.sounds = {
            'bounce': pygame.mixer.Sound('bounce.wav')
        }

        # Set up the app window.
        pygame.display.set_caption('Game of the Amazons')
        pygame.display.set_icon(self.surfaces['app_icon'])

        # Initialize game state.
        self.msg = ''
        self.mouse = { 'x':0, 'y':0 }
        self.quitting = False
        self.world_x = 0 # Coordinates we are at in the game world.
        self.world_y = 0
        self.movement_vector = { 'x': 0, 'y': 0 } # Camera movement vector.

        # Create and start GUI.
        gui_app = gui.App()

        self.title_gui = self.TitleGUI(runner=self)
        self.game_gui = self.GameGUI(runner=self)

        self.gui_cont = gui.Container(align=-1,valign=-1)
        self.gui_cont.add(self.title_gui,
                          (self.screen_w / 2) - 160,
                          (.8 * self.screen_h))

        gui_app.init(self.gui_cont)
        self.gui_app = gui_app

        # Start the game app.
        pygame.mouse.set_visible(False) # We'll use our custom cursor instead.

        self.game_loop()

        pygame.mouse.set_visible(True)

        pygame.quit()
        sys.exit(0)

    def game_loop(self):
        """Run the main game loop until the player quits."""
        while not self.quitting:
            # Update game state.
            if self.phase == self.PHASE_TRANSITION:
                # Slide to the board.
                self.world_y = int(self.interpolated_x_at_time(0.0, 
                                                               self.screen_h, 
                                                               15.0,
                                                               float(self.transition_tick)))
                self.transition_tick += 1
                if (self.transition_tick == 15):
                    self.world_y = self.screen_h
                    self.gui_cont.add(self.game_gui,
                          self.get_board_x() + self.get_board_w() + 10,
                          self.get_board_y() + self.get_board_h() - 10 -
                          self.game_gui.height)
                    self.start_current_move()
            elif self.phase == self.PHASE_TRANSITION_BACK:
                # Slide back to the title screen.
                self.world_y = (self.screen_h -
                                int(self.interpolated_x_at_time(0.0,
                                                                self.screen_h,
                                                                15.0,
                                                                float(self.transition_tick))))
                self.transition_tick += 1
                if (self.transition_tick == 15):
                    self.world_y = 0
                    self.set_phase(self.PHASE_TITLE)
                    self.gui_cont.add(self.title_gui,
                          (self.screen_w / 2) - 160,
                          (.8 * self.screen_h))

            elif self.phase in (self.PHASE_PICK_AMAZON, self.PHASE_PLACE_AMAZON,
                self.PHASE_SHOOT_ARROW, self.PHASE_WAIT_FOR_AI):
                # End game if the clock runs out.
                g = self.game
                b = g.board
                if ((b.to_move == 'white' and self.w_clock != None and
                    self.w_clock.is_over) or (b.to_move == 'black' and
                    self.b_clock != None and self.b_clock.is_over)):
                    g.move('time_over')
                    self.start_current_move()
                    self.sounds['bounce'].play()

            if self.phase == self.PHASE_WAIT_FOR_AI:
                # Check if the AI is ready to move.
                board = self.game.board
                curr_player = (self.white_player if (board.to_move == "white")
                       else self.black_player)
                m = curr_player.next_move()
                if m != None:
                    self.game.move(m)
                    self.start_current_move()
                    if self.game.is_over:
                        print 'Board:'
                        print str(self.game.board)
                        print 'Valid moves: ' + str(self.game.board.get_valid_moves())
                    self.sounds['bounce'].play()

            self.render()

            self.process_inputs()

            self.fpsClock.tick(30)

    def process_inputs(self):
        """Process player input for one tick of the game."""
        for event in pygame.event.get():
            self.gui_app.event(event) # Let the GUI know about it.
            if event.type == QUIT:
                self.quitting = True

            elif event.type == MOUSEMOTION:
                self.mouse['x'], self.mouse['y'] = event.pos

            elif event.type == MOUSEBUTTONDOWN:
                self.mouse['x'], self.mouse['y'] = event.pos
                if event.button == 1:
                    if self.phase == self.PHASE_PICK_AMAZON:
                        self.pick_amazon()
                        if self.amazon_in_hand != None:
                            self.is_dragging = True

            elif event.type == MOUSEBUTTONUP:
                self.mouse['x'], self.mouse['y'] = event.pos
                if event.button == 1:
                    if self.is_dragging:
                        self.drop_amazon()
                    elif self.phase == self.PHASE_PICK_AMAZON:
                        self.pick_amazon()
                    elif self.phase == self.PHASE_PLACE_AMAZON:
                        self.place_amazon()
                    elif self.phase == self.PHASE_SHOOT_ARROW:
                        self.shoot_arrow()

            elif event.type == KEYUP:
                if event.key == K_ESCAPE:
                    if self.phase in (self.PHASE_PLACE_AMAZON,
                                         self.PHASE_SHOOT_ARROW):
                        # Reset current move.
                        self.start_current_move()
                    else:
                        pygame.event.post(pygame.event.Event(QUIT))

    def on_new_game(self):
        gs = self.game_settings
        s = self.app_settings

        # Instantiate game and players.
        self.game = Game(gs['width'], gs['height'], gs['white_amazons'],
                         gs['black_amazons'], gs['arrows'], gs['to_move'])

        self.white_player = (Player(WHITE) if s['w_player'] == 'human' else
                             AIPlayer(WHITE, difficulty = s['w_difficulty']))
        self.black_player = (Player(BLACK) if s['b_player'] == 'human' else
                             AIPlayer(BLACK, difficulty = s['b_difficulty']))

        # Instantiate clocks.
        w_use_clock = s['w_use_fixed_time'] or s['w_use_byoyomi']
        w_minutes = w_seconds = w_periods = w_p_seconds = 0
        if s['w_use_fixed_time']:
            w_minutes = s['w_minutes']
            w_seconds = s['w_seconds']
        if s['w_use_byoyomi']:
            w_periods = s['w_byoyomi_periods']
            w_p_seconds = s['w_byoyomi_seconds']
        self.w_clock = (Clock(w_minutes, w_seconds, w_periods, w_p_seconds)
            if w_use_clock else None)

        b_use_clock = s['b_use_fixed_time'] or s['b_use_byoyomi']
        b_minutes = b_seconds = b_periods = b_p_seconds = 0
        if s['b_use_fixed_time']:
            b_minutes = s['b_minutes']
            b_seconds = s['b_seconds']
        if s['b_use_byoyomi']:
            b_periods = s['b_byoyomi_periods']
            b_p_seconds = s['b_byoyomi_seconds']
        self.b_clock = (Clock(b_minutes, b_seconds, b_periods, b_p_seconds)
            if b_use_clock else None)

        # Update GUI.
        try:
            self.gui_cont.remove(self.title_gui)
        except ValueError: # not in list
            pass

        # Update Phase.
        self.phase = self.PHASE_TRANSITION
        self.transition_tick = 0

    def back_to_title(self, *args):
        self.set_phase(self.PHASE_TRANSITION_BACK)
        self.transition_tick = 0

    def set_phase(self, new_phase):
        """
        Sets the current phase to the specified value and adjusts the
        main message as appropriate.
        """
        board = self.game.board
        self.phase = new_phase
        if new_phase == self.PHASE_PICK_AMAZON:
            self.msg = board.to_move.capitalize() + ', pick an amazon to move.'
        elif new_phase == self.PHASE_WAIT_FOR_AI:
            self.msg = board.to_move.capitalize() + ' is thinking...'
        elif new_phase == self.PHASE_WAIT_FOR_REMOTE:
            self.msg = board.to_move.capitalize() + ': waiting for remote player'
        elif new_phase == self.PHASE_PLACE_AMAZON:
            self.msg = board.to_move.capitalize()+', pick a square to move to.'
        elif new_phase == self.PHASE_SHOOT_ARROW:
            self.msg = board.to_move.capitalize() + ', shoot an arrow.'
        elif new_phase == self.PHASE_GAME_OVER:
            self.msg = "Game Over: %s wins!" % self.game.winner.capitalize()
        else:
            self.msg = ""
        self.game_gui.do_layout(new_phase)
        try:
            self.gui_cont.remove(self.game_gui)
        except ValueError: # game_gui not in gui container - that's fine
            pass
        if new_phase in (self.PHASE_PICK_AMAZON, self.PHASE_PLACE_AMAZON,
                         self.PHASE_SHOOT_ARROW, self.PHASE_WAIT_FOR_AI,
                         self.PHASE_GAME_OVER, self.PHASE_WAIT_FOR_REMOTE):
            self.gui_cont.add(self.game_gui,
                          self.get_board_x() + self.get_board_w() + 10,
                          self.get_board_y() + self.get_board_h() - 10 -
                          self.game_gui.height)

    def start_current_move(self):
        """
        Chooses the appropriate phase given the current player (human or AI).
        """
        self.amazon_in_hand = None
        self.amazon_target = None
        self.is_dragging = False
        board = self.game.board
        if (self.game.is_over):
            if self.w_clock != None: self.w_clock.stop()
            if self.b_clock != None: self.b_clock.stop()
            self.set_phase(self.PHASE_GAME_OVER)
            return
        curr_player = (self.white_player if (board.to_move == "white") 
                       else self.black_player)
        if isinstance(curr_player, AIPlayer):
            self.set_phase(self.PHASE_WAIT_FOR_AI)
            self.switch_clock()
            self.sounds['bounce'].play()
            curr_player.start_thinking(self.game.board)
        elif isinstance(curr_player, NetworkPlayer):
            self.set_phase(self.PHASE_WAIT_FOR_REMOTE)
            try:
                self.game.move(curr_player.next_move(self.game))
            except ValueError:
                self.start_current_move()
                return
            self.set_phase(self.PHASE_PICK_AMAZON)
        else:
            self.set_phase(self.PHASE_PICK_AMAZON)

        self.switch_clock()

    def switch_clock(self):
        """Hit the game clock switch."""
        board = self.game.board
        if (board.to_move == "white"):
            if self.w_clock != None: self.w_clock.start()
            if self.b_clock != None: self.b_clock.stop()
        else:
            if self.w_clock != None: self.w_clock.stop()
            if self.b_clock != None: self.b_clock.start()

    def pick_amazon(self):
        """Pick the amazon at the current cursor position to move."""
        sq = self.get_cursor_square()
        if sq == None:
            return
        board = self.game.board
        sq = Square(sq)
        if sq in board.current_amazons:
            self.amazon_in_hand = Square(sq)
            self.set_phase(self.PHASE_PLACE_AMAZON)

    def drop_amazon(self):
        """Drop an amazon you had been mouse-dragging."""
        self.is_dragging = False
        sq = self.get_cursor_square()
        if sq == None:
            # Dropped outside the board - cancel drag and restart current move.
            self.start_current_move()
            return
        board = self.game.board
        sq = Square(sq)
        if (sq == self.amazon_in_hand):
            # User clicked and released on an amazon - keep that amazon picked.
            return
        elif board.is_path_clear(self.amazon_in_hand, sq):
            # User released on a valid square - choose it as target and move on.
            self.amazon_target = sq
            self.set_phase(self.PHASE_SHOOT_ARROW)
        else:
            # User released on an invalid square.  Restart current move.
            self.start_current_move()

    def place_amazon(self):
        """Choose a target square to move the amazon in hand."""
        sq = self.get_cursor_square()
        board = self.game.board
        if sq == None:
            self.start_current_move() # Invalid square.  Restart current move.
            return
        sq = Square(sq)
        if board.is_path_clear(self.amazon_in_hand, sq):
            self.amazon_target = sq
            self.set_phase(self.PHASE_SHOOT_ARROW)
        else:
            self.start_current_move() # Invalid square.  Restart current move.
            return

    def shoot_arrow(self):
        """Choose a target square to shoot an arrow and execute a move."""
        sq = self.get_cursor_square()
        board = self.game.board
        if sq == None:
            self.start_current_move() # Invalid square.  Restart current move.
            return
        sq = Square(sq)
        if board.is_path_clear(self.amazon_target, sq, ignore=self.amazon_in_hand):
            arrow_target = sq
            mv = Move(self.amazon_in_hand, self.amazon_target, arrow_target)
            if board.check_is_move_valid(mv):
                self.game.move(mv)
                curr_player = (self.white_player if (board.to_move == "white")
                       else self.black_player)
                if hasattr(curr_player,'send_my_move'):
                    curr_player.send_my_move(mv)
                self.start_current_move()
                self.sounds['bounce'].play()
                return
        else:
            self.start_current_move() # Invalid square.  Restart current move.
            return

    def resign(self):
        self.game.move('resign')
        self.start_current_move()
        self.sounds['bounce'].play()


    # RENDERING ###############################################################

    def render(self):
        """Render the current game state to screen."""
        window = self.window
        window.fill(self.colors['black'])

        self.render_background()

        self.render_title()

        self.render_board()

        if self.phase in (self.PHASE_PICK_AMAZON, self.PHASE_PLACE_AMAZON,
                          self.PHASE_SHOOT_ARROW):
            self.render_indicators()

        self.render_clocks()

        self.gui_app.paint()

        self.render_cursor()

        pygame.display.update()

    def render_cursor(self):
        board = self.game.board
        c_surf = self.surfaces['cursor']
        if self.phase == self.PHASE_PLACE_AMAZON:
            c_surf = (self.surfaces['white_cursor'] if board.to_move == 'white'
                      else self.surfaces['black_cursor'])
        elif self.phase == self.PHASE_SHOOT_ARROW:
            c_surf = self.surfaces['arrow_cursor']
        self.blit_clipped(c_surf, self.mouse['x'], self.mouse['y'])

    def render_background(self):
        """Draw the stone table top background."""
        window = self.window
        stone_surf = self.surfaces['stone']
        # Figure out how many 800x800 tiles we need.
        tiles_x = int(self.screen_w / 800) + 2
        tiles_y = int(self.screen_h / 800) + 2
        start_x = (self.world_x % 800) * -1
        start_y = (self.world_y % 800) * -1
        for i in range(tiles_y):
            for j in range(tiles_x):
                self.blit_clipped(stone_surf,
                                  start_x + (j*800),
                                  start_y + (i*800))

    def render_title(self):
        """Draw the title screen."""
        window = self.window
        t_surf = self.surfaces['title']
        x = (self.screen_w / 2) - (t_surf.get_width() / 2)
        y = (self.screen_h / 2) - (t_surf.get_height() / 2)
        self.blit_clipped(t_surf, x - self.world_x, y - self.world_y)

    def render_board(self):
        """
        Draw the board and all game pieces.
        Remember vertical pixel coordinates use an inverted axis (down is
        positive) compared to the Board class's y coordinates (up is positive).
        """
        board = self.game.board
        board_surf = self.surfaces['board']
        board_w = board_surf.get_width()
        board_h = board_surf.get_height()
        board_x = self.get_board_x()
        board_y = self.get_board_y()
        self.blit_clipped(board_surf, board_x, board_y)

        # Draw amazons.
        amz_surf = self.surfaces['white']
        for amz in board.white_amazons:
            amz_x, amz_y = self.get_screen_pos(amz.x, amz.y)
            if (self.amazon_in_hand == None or self.amazon_in_hand != amz):
                self.blit_clipped(amz_surf, amz_x, amz_y)
        amz_surf = self.surfaces['black']
        for amz in board.black_amazons:
            amz_x, amz_y = self.get_screen_pos(amz.x, amz.y)
            if (self.amazon_in_hand == None or self.amazon_in_hand != amz):
                self.blit_clipped(amz_surf, amz_x, amz_y)

        # Draw arrows.
        arr_surf = self.surfaces['arrow']
        for arr in board.arrows:
            arr_x = BORDER_PX + (arr[0] * SQUARE_PX)
            arr_y = board_h - (BORDER_PX + SQUARE_PX + (arr[1] * SQUARE_PX))
            self.blit_clipped(arr_surf, board_x + arr_x, board_y + arr_y)

        # Draw last move.
        last_surf = self.surfaces['last_move']
        last_mv = self.game.last_move
        if last_mv != None:
            for sq in last_mv:
                last_x, last_y = self.get_screen_pos(sq.x, sq.y)
                self.blit_clipped(last_surf, last_x, last_y)

        # Draw message.
        self.render_text_centered(self.msg, (self.screen_w / 2), 10)

        # TODO Draw territory if the option is on.

    def render_text_centered(self, text, x_center, y):
        font = self.fonts['comicsansms']
        msg_surf = font.render(text, False, self.colors['white'])
        msg_rect = msg_surf.get_rect()
        self.render_text(text, x_center - (msg_rect.width / 2), y)

    def render_text(self, text, x, y):
        font = self.fonts['comicsansms']
        msg_surf = font.render(text, False, self.colors['white'])
        msg_rect = msg_surf.get_rect()
        msg_rect.topleft = (x, y)
        shadow_surf = font.render(text, False, self.colors['black'])
        shadow_rect = shadow_surf.get_rect()
        shadow_rect.topleft = (x + 2, y + 2)
        self.window.blit(shadow_surf, shadow_rect)
        self.window.blit(msg_surf, msg_rect)

    def render_indicators(self):
        """
        Draw circles and squares indicating legal/illegal clicks, and hazy_white
        pieces to indicate amazons chosen for movement.
        """
        if self.phase == self.PHASE_WAIT_FOR_AI:
            return

        # Draw hazy pieces.
        board = self.game.board
        hazy_surf = (self.surfaces['hazy_white'] if board.to_move == "white"
                     else self.surfaces['hazy_black'])

        if (self.phase in (self.PHASE_PLACE_AMAZON, self.PHASE_SHOOT_ARROW)):
            hazy_x, hazy_y = self.get_screen_pos(self.amazon_in_hand.x,
                                                 self.amazon_in_hand.y)
            self.blit_clipped(hazy_surf, hazy_x, hazy_y)

        if self.phase == self.PHASE_SHOOT_ARROW:
            hazy_x, hazy_y = self.get_screen_pos(self.amazon_target.x,
                                                 self.amazon_target.y)
            self.blit_clipped(hazy_surf, hazy_x, hazy_y)

        # Draw x or circle indicating if the hovered square is a valid target.
        c_square = self.get_cursor_square()
        if (c_square == None):
            return
        c_square = Square(c_square)
        indicator_pos = self.get_screen_pos(c_square[0], c_square[1])
        is_legal = False
        if self.phase == self.PHASE_PICK_AMAZON:
            is_legal = c_square in board.current_amazons
        elif self.phase == self.PHASE_PLACE_AMAZON:
            is_legal = board.is_path_clear(self.amazon_in_hand, c_square)
        elif self.phase == self.PHASE_SHOOT_ARROW:
            is_legal = board.is_path_clear(self.amazon_target, c_square, 
                                           ignore=self.amazon_in_hand)
        surf = self.surfaces['circle'] if is_legal else self.surfaces['x']
        self.blit_clipped(surf,
                          indicator_pos[0],
                          indicator_pos[1])

    def render_clocks(self):
        """
        Draw the remaining time for each player to the right of the board.
        """
        w_clock = self.w_clock
        b_clock = self.b_clock
        if (w_clock == None and b_clock == None):
            return
        line_height = 28
        indent = 30
        x = self.get_board_x() + self.get_board_w() + 10
        y = self.get_board_y() + (self.get_board_h() / 2) - (4 * line_height)
        self.render_text('White Time:', x, y)
        if (w_clock == None):
            self.render_text('Untimed', x + indent, y + line_height)
        else:
            if w_clock.has_fixed_time and w_clock.has_periods:
                s = '{:d}:{:0>2d}'.format(w_clock.minutes, w_clock.seconds)
                self.render_text(s, x + indent, y + line_height)
                s = '+ {:d} x {:0>2d}'.format(w_clock.periods,
                    w_clock.period_seconds)
                self.render_text(s, x + indent, y + (2*line_height))
            elif w_clock.has_fixed_time:
                s = '{:d}:{:0>2d}'.format(w_clock.minutes, w_clock.seconds)
                self.render_text(s, x + indent, y + line_height)
            elif w_clock.has_periods:
                s = '{:d} x {:0>2d}'.format(w_clock.periods,
                    w_clock.period_seconds)
                self.render_text(s, x + indent, y + line_height)
        y += 4 * line_height
        self.render_text('Black Time:', x, y)
        if (b_clock == None):
            self.render_text('Untimed', x + indent, y + line_height)
        else:
            if b_clock.has_fixed_time and b_clock.has_periods:
                s = '{:d}:{:0>2d}'.format(b_clock.minutes, b_clock.seconds)
                self.render_text(s, x + indent, y + line_height)
                s = '+ {:d} x {:0>2d}'.format(b_clock.periods,
                    b_clock.period_seconds)
                self.render_text(s, x + indent, y + (2*line_height))
            elif b_clock.has_fixed_time:
                s = '{:d}:{:0>2d}'.format(b_clock.minutes, b_clock.seconds)
                self.render_text(s, x + indent, y + line_height)
            elif b_clock.has_periods:
                s = '{:d} x {:0>2d}'.format(b_clock.periods,
                    b_clock.period_seconds)
                self.render_text(s, x + indent, y + line_height)


    def blit_clipped(self, surface, x, y):
        """
        Blits the specified surface to the main window, automatically clipping
        it if it starts off the upper or left sides of the window.
        """
        # Nothing to blit if the surface is off the right/bottom sides.
        if x > self.screen_w or y > self.screen_h:
            return
        source_area = pygame.Rect(0, 0, surface.get_width(), surface.get_height())
        dest_x = x
        dest_y = y
        if x < 0:
            dest_x = 0
            clipped_x = x * -1
            if clipped_x >= surface.get_width():
                return # The entire surface is off the left side of the window.
            source_area.left = clipped_x
            source_area.width = surface.get_width() - clipped_x
        if y < 0:
            dest_y = 0
            clipped_y = y * -1
            if clipped_y >= surface.get_height():
                return # The entire surface is off the top of the window.
            source_area.top = clipped_y
            source_area.height = surface.get_height() - clipped_y

        self.window.blit(surface, (dest_x, dest_y), source_area)


    # GUI #####################################################################

    class TitleGUI(gui.Table):
        def __init__(self,**kwargs):
            gui.Table.__init__(self, **kwargs)
            runner = kwargs['runner']
            self.tr()
            class NewGameButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'New Game'
                    gui.Button.__init__(self, **kwargs)
                    self.connect(gui.CLICK, runner.on_new_game)
            e = NewGameButton()
            self.td(e)
            self.tr()
            class HostRemoteButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'New Game - Wait for Remote Player'
                    gui.Button.__init__(self, **kwargs)
                    self.connect(gui.CLICK, self.on_click, None)
                def on_click(self, *args):
                    host_d = PygameRunner.HostRemoteDialog(runner)
                    host_d.open()
            e = HostRemoteButton()
          
            self.td(e)
            self.tr()
            class ConnectRemoteButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = "New Game - Connect to Remote Player"
                    gui.Button.__init__(self, **kwargs)
                    self.connect(gui.CLICK, self.on_click, None)
                def on_click(self, *args):
                    connect_d = PygameRunner.ConnectToRemoteDialog(runner)
                    connect_d.open()
                        
            e = ConnectRemoteButton()
            self.td(e)
            self.tr()df
            e = gui.Button('Rules')
            self.td(e)
            self.tr()
            self.tr()
            class OptionsButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'Options'
                    gui.Button.__init__(self, **kwargs)
                    self.connect(gui.CLICK,self.on_click,None)
                def on_click(self, *args):
                    s = runner.app_settings
                    options_d = PygameRunner.OptionsDialog(settings=s)
                    options_d.open()
            e = OptionsButton()
            self.td(e)
            self.tr()
            def post_quit():
                pygame.event.post(pygame.event.Event(QUIT))
            quit_d = PygameRunner.ConfirmDialog(title='Confirm Quit',
                                                msg='Are you sure you want to quit?',
                                                confirm='Quit',
                                                confirm_func=post_quit)
            class QuitButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'Quit'
                    gui.Button.__init__(self, **kwargs)
                    self.connect(gui.CLICK,quit_d.open,None)
            e = QuitButton()
            self.td(e)

    class GameGUI(gui.Container):
        def __init__(self,**kwargs):
            kwargs['width'] = 100
            kwargs['height'] = 160
            gui.Container.__init__(self, **kwargs)
            runner = kwargs['runner']

            self.table = gui.Table()
            self.add(self.table, 0, 0)

            self.height = 0

            self.undo_button = gui.Button('Undo')
            self.undo_button.is_visible = False

            self.continue_button = gui.Button('Continue')
            self.continue_button.is_visible = False

            class ResignButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'Resign'
                    gui.Button.__init__(self, **kwargs)
                    self.is_visible = False
                    self.connect(gui.CLICK, self.on_click)
                def on_click(self):
                    PygameRunner.ConfirmDialog(title='Confirm Resign',
                                               msg='Are you sure you want to resign?',
                                               confirm='Resign',
                                               confirm_func=runner.resign).open()
            self.resign_button = ResignButton()

            self.play_again_button = gui.Button('Play Again')
            self.play_again_button.is_visible = False

            class OptionsButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'Options'
                    gui.Button.__init__(self, **kwargs)
                    self.is_visible = False
                    self.connect(gui.CLICK,self.on_click)
                def on_click(self, *args):
                    s = runner.app_settings
                    options_d = PygameRunner.OptionsDialog(settings=s)
                    options_d.open()
            self.options_button = OptionsButton()

            class TitleMenuButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'Title Menu'
                    gui.Button.__init__(self, **kwargs)
                    self.is_visible = False
                    self.connect(gui.CLICK, self.on_click, None)
                def on_click(self, *args):
                    if runner.game.is_over:
                        runner.back_to_title()
                    else:
                        PygameRunner.ConfirmDialog(title='Confirm End Game',
                            msg='Are you sure you want to end the game ' +\
                                'and return to the title menu?',
                            confirm='End Game',
                            confirm_func=runner.back_to_title).open()
            self.title_menu_button = TitleMenuButton()

            def post_quit():
                pygame.event.post(pygame.event.Event(QUIT))
            class QuitButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'Quit'
                    gui.Button.__init__(self, **kwargs)
                    self.is_visible = False
                    self.connect(gui.CLICK,self.on_click)
                def on_click(self):
                    PygameRunner.ConfirmDialog(title='Confirm Quit',
                                               msg='Are you sure you want to quit?',
                                               confirm='Quit',
                                               confirm_func=post_quit).open()
            self.quit_button = QuitButton()

        def add_button(self, table, button):
            button.is_visible = True
            table.tr()
            table.td(button)
            self.height += 20

        def do_layout(self, phase):
            # Decide which game menu buttons should be visible based on
            # current game phase.
            self.undo_button.is_visible = False
            self.continue_button.is_visible = False
            self.resign_button.is_visible = False
            self.play_again_button.is_visible = False
            self.options_button.is_visible = False
            self.title_menu_button.is_visible = False
            self.quit_button.is_visible = False

            self.remove(self.table)
            self.height = 0
            self.table = gui.Table()
            t = self.table
            PR = PygameRunner

            if (phase in (PR.PHASE_WAIT_FOR_AI, PR.PHASE_WAIT_FOR_REMOTE)):
                self.add_button(t, self.options_button)
                self.add_button(t, self.title_menu_button)
                self.add_button(t, self.quit_button)
            elif (phase in (PR.PHASE_PICK_AMAZON, PR.PHASE_PLACE_AMAZON,
                            PR.PHASE_SHOOT_ARROW)):
                self.add_button(t, self.resign_button)
                self.add_button(t, self.options_button)
                self.add_button(t, self.title_menu_button)
                self.add_button(t, self.quit_button)
            elif (phase == PR.PHASE_GAME_OVER):
                self.add_button(t, self.options_button)
                self.add_button(t, self.title_menu_button)
                self.add_button(t, self.quit_button)

            self.add(t, 0, 0)

    class OptionsDialog(gui.Dialog):
        def __init__(self, **kwargs):
            dialog = self
            title = gui.Label('Options')
            f = gui.Form()
            s = kwargs['settings']

            c = gui.Container(width=340, height=550)
            c.add(gui.Label('White Player'), 0, 0)
            w_is_human = s['w_player'] == 'human'
            w_player_group = gui.Group(name='w_player_group',
                                       value=s['w_player'])
            w_human_button = gui.Radio(w_player_group, 'human')
            c.add(w_human_button, 20, 20)
            c.add(gui.Label('Human'), 40, 20)
            w_ai_button = gui.Radio(w_player_group, 'ai')
            c.add(w_ai_button, 20, 40)
            c.add(gui.Label('AI'), 40, 40)
            w_diff_label = gui.Label('Difficulty: ' + str(s['w_difficulty']))
            w_diff_label.disabled = w_is_human
            c.add(w_diff_label, 40, 60)
            w_diff_slider = gui.HSlider(value=s['w_difficulty'],min=1,max=10,
                                        size=1,width=120,name='w_diff_slider')
            w_diff_slider.disabled = w_is_human
            c.add(w_diff_slider, 40, 80)
            c.add(gui.Label('Clock'), 20, 100)
            w_use_fixed_time = s['w_use_fixed_time']
            w_fixed_time_switch = gui.Switch(w_use_fixed_time,
                                             name='w_use_fixed_time')
            c.add(w_fixed_time_switch, 40, 120)
            w_fixed_time_label = gui.Label(' Use Fixed Time: ')
            w_fixed_time_label.disabled = not w_use_fixed_time
            c.add(w_fixed_time_label, 60, 120)
            w_fixed_minutes = gui.TextArea(value=str(s['w_minutes']),
                                           size=2, width=20, height=20,
                                           name='w_fixed_minutes')
            w_fixed_minutes.disabled = not w_use_fixed_time
            c.add(w_fixed_minutes, 195, 120)
            w_fixed_minutes_label = gui.Label(':')
            w_fixed_minutes_label.disabled = not w_use_fixed_time
            c.add(w_fixed_minutes_label, 230, 120)
            w_seconds_str = '{:0>2d}'.format(int(s['w_seconds']))
            w_fixed_seconds = gui.TextArea(value=w_seconds_str,
                                           size=2, width=20, height=20,
                                           name='w_fixed_seconds')
            w_fixed_seconds.disabled = not w_use_fixed_time
            c.add(w_fixed_seconds, 240, 120)
            w_use_byoyomi = s['w_use_byoyomi']
            w_byoyomi_switch = gui.Switch(value=w_use_byoyomi,
                                          name='w_use_byoyomi')
            c.add(w_byoyomi_switch, 40, 150)
            w_byoyomi_label = gui.Label(' Add Byo-yomi Periods: ')
            w_byoyomi_label.disabled = not w_use_byoyomi
            c.add(w_byoyomi_label, 60, 150)
            w_byoyomi_periods = gui.TextArea(str(s['w_byoyomi_periods']),
                                             size=2, width=20, height=20,
                                             name='w_byoyomi_periods')
            w_byoyomi_periods.disabled = not w_use_byoyomi
            c.add(w_byoyomi_periods, 65, 170)
            w_byoyomi_periods_label = gui.Label(' periods of ')
            w_byoyomi_periods_label.disabled = not w_use_byoyomi
            c.add(w_byoyomi_periods_label, 95, 170)
            w_byoyomi_seconds = gui.TextArea(str(s['w_byoyomi_seconds']),
                                             size=2, width=20, height=20,
                                             name='w_byoyomi_seconds')
            w_byoyomi_seconds.disabled = not w_use_byoyomi
            c.add(w_byoyomi_seconds, 185, 170)
            w_byoyomi_seconds_label = gui.Label(' seconds each')
            w_byoyomi_seconds_label.disabled = not w_use_byoyomi
            c.add(w_byoyomi_seconds_label, 215, 170)

            c.add(gui.Label('Black Player'), 0, 200)
            b_is_human = s['b_player'] == 'human'
            b_player_group = gui.Group(name='b_player_group',
                                       value=s['b_player'])
            b_human_button = gui.Radio(b_player_group, 'human')
            c.add(b_human_button, 20, 220)
            c.add(gui.Label('Human'), 40, 220)
            b_ai_button = gui.Radio(b_player_group, 'ai')
            c.add(b_ai_button, 20, 240)
            c.add(gui.Label('AI'), 40, 240)
            b_diff_label = gui.Label('Difficulty: ' + str(s['b_difficulty']))
            b_diff_label.disabled = b_is_human
            c.add(b_diff_label, 40, 260)
            b_diff_slider = gui.HSlider(value=s['b_difficulty'],min=1,max=10,
                                        size=1,width=120,name='b_diff_slider')
            w_diff_slider.disabled = b_is_human
            c.add(b_diff_slider, 40, 280)
            c.add(gui.Label('Clock'), 20, 300)
            b_use_fixed_time = s['b_use_fixed_time']
            b_fixed_time_switch = gui.Switch(value=b_use_fixed_time,
                                             name='b_use_fixed_time')
            c.add(b_fixed_time_switch, 40, 320)
            b_fixed_time_label = gui.Label(' Use Fixed Time: ')
            b_fixed_time_label.disabled = not b_use_fixed_time
            c.add(b_fixed_time_label, 60, 320)
            b_fixed_minutes = gui.TextArea(value=str(s['b_minutes']), size=2,
                                           width=20, height=20,
                                           name='b_fixed_minutes')
            b_fixed_minutes.disabled = not b_use_fixed_time
            c.add(b_fixed_minutes, 195, 320)
            b_fixed_minutes_label = gui.Label(':')
            b_fixed_minutes_label.disabled = not b_use_fixed_time
            c.add(b_fixed_minutes_label, 230, 320)
            b_seconds_str = '{:0>2d}'.format(int(s['b_seconds']))
            b_fixed_seconds = gui.TextArea(value=b_seconds_str, size=2,
                                           width=20,height=20,
                                           name='b_fixed_seconds')
            b_fixed_seconds.disabled = not b_use_fixed_time
            c.add(b_fixed_seconds, 240, 320)
            b_use_byoyomi = s['b_use_byoyomi']
            b_byoyomi_switch = gui.Switch(value=b_use_byoyomi,
                                          name='b_use_byoyomi')
            c.add(b_byoyomi_switch, 40, 350)
            b_byoyomi_label = gui.Label(' Add Byo-yomi Periods: ')
            b_byoyomi_label.disabled = not b_use_byoyomi
            c.add(b_byoyomi_label, 60, 350)
            b_byoyomi_periods = gui.TextArea(value=str(s['b_byoyomi_periods']),
                                             size=2, width=20, height=20,
                                             name='b_byoyomi_periods')
            b_byoyomi_periods.disabled = not b_use_byoyomi
            c.add(b_byoyomi_periods, 65, 370)
            b_byoyomi_periods_label = gui.Label(' periods of ')
            b_byoyomi_periods_label.disabled = not b_use_byoyomi
            c.add(b_byoyomi_periods_label, 95, 370)
            b_byoyomi_seconds = gui.TextArea(value=str(s['b_byoyomi_seconds']),
                                             size=2, width=20, height=20,
                                             name='b_byoyomi_seconds')
            b_byoyomi_seconds.disabled = not b_use_byoyomi
            c.add(b_byoyomi_seconds, 185, 370)
            b_byoyomi_seconds_label = gui.Label(' seconds each')
            b_byoyomi_seconds_label.disabled = not b_use_byoyomi
            c.add(b_byoyomi_seconds_label, 215, 370)

            c.add(gui.Label('Board'), 0, 400)
            territory_marking = s['territory_marking']
            territory_group = gui.Group(name='territory_group',
                                        value=territory_marking)
            no_territory_button = gui.Radio(territory_group,
                                            TERRITORY_MARK_NONE)
            c.add(no_territory_button, 20, 420)
            c.add(gui.Label('No Territory Markings'), 40, 420)
            secured_territory_button = gui.Radio(territory_group,
                                                 TERRITORY_MARK_SECURED)
            c.add(secured_territory_button, 20, 440)
            c.add(gui.Label('Show Secured Territory'), 40, 440)
            estimated_territory_button = gui.Radio(territory_group,
                                                   TERRITORY_MARK_ESTIMATED)
            c.add(estimated_territory_button, 20, 460)
            c.add(gui.Label('Show Estimated Territory'), 40, 460)

            show_ai_details_switch = gui.Switch(value=s['show_ai_details'],
                                                name='show_ai_details')
            c.add(show_ai_details_switch, 0, 490)
            show_ai_details_label = gui.Label(' Show AI Details')
            show_ai_details_label.disabled = not s['show_ai_details']
            c.add(show_ai_details_label, 20, 490)

            cancel_button = gui.Button('Cancel', width=70)
            c.add(cancel_button, (c.rect.w / 2) - 90, 525)
            apply_button = gui.Button('Apply', width=70)
            c.add(apply_button, (c.rect.w / 2) + 10, 525)

            def diff_changed(slider, label):
                val = slider.value
                label.set_text('Difficulty: ' + str(val))
            w_diff_slider.connect(gui.CHANGE, diff_changed,
                                  w_diff_slider, w_diff_label)
            b_diff_slider.connect(gui.CHANGE, diff_changed,
                                  b_diff_slider, b_diff_label)
            def set_ai_enabled(player_group, diff_label, diff_slider):
                val = player_group.value == 'ai'
                diff_label.disabled = not val
                diff_slider.disabled = not val
            w_player_group.connect(gui.CHANGE, set_ai_enabled, w_player_group,
                                   w_diff_label, w_diff_slider)
            b_player_group.connect(gui.CHANGE, set_ai_enabled, b_player_group,
                                   b_diff_label, b_diff_slider)
            def fixed_time_switch_changed(switch, fixed_time_label,
                                          fixed_minutes, fixed_minutes_label,
                                          fixed_seconds):
                val = switch.value
                fixed_time_label.disabled = not val
                fixed_minutes.disabled = not val
                fixed_minutes_label.disabled = not val
                fixed_seconds.disabled = not val
            w_fixed_time_switch.connect(gui.CHANGE, fixed_time_switch_changed,
                                        w_fixed_time_switch,
                                        w_fixed_time_label, w_fixed_minutes,
                                        w_fixed_minutes_label, w_fixed_seconds)
            b_fixed_time_switch.connect(gui.CHANGE, fixed_time_switch_changed,
                                        b_fixed_time_switch,
                                        b_fixed_time_label, b_fixed_minutes,
                                        b_fixed_minutes_label, b_fixed_seconds)
            def time_changed(textarea, default_val, min_val, max_val):
                val = textarea.value
                try:
                    i = int(val)
                    if i < min_val:
                        textarea.value = str(min_val)
                    if i > max_val:
                        textarea.value = str(max_val)
                except ValueError:
                    textarea.value = default_val
                textarea.value = textarea.value.strip()
                if len(textarea.value) < 2:
                    textarea.value = '{:0>2d}'.format(int(textarea.value))
                # Special validation - check times > 00:00.
                if (int(w_fixed_minutes.value) +
                    int(w_fixed_seconds.value)) <= 0:
                    w_fixed_seconds.value = '01'
                if (int(b_fixed_minutes.value) +
                    int(b_fixed_seconds.value)) <= 0:
                    b_fixed_seconds.value = '01'                

            w_fixed_minutes.connect(gui.BLUR, time_changed, w_fixed_minutes,
                                    20, 0, 9999)
            w_fixed_seconds.connect(gui.BLUR, time_changed, w_fixed_seconds,
                                    0, 0, 59)
            w_byoyomi_periods.connect(gui.BLUR, time_changed, w_byoyomi_periods,
                                      3, 1, 9999)
            w_byoyomi_seconds.connect(gui.BLUR, time_changed, w_byoyomi_seconds,
                                      30, 1, 9999)
            b_fixed_minutes.connect(gui.BLUR, time_changed, b_fixed_minutes,
                                    20, 0, 9999)
            b_fixed_seconds.connect(gui.BLUR, time_changed, b_fixed_seconds,
                                    0, 0, 59)
            b_byoyomi_periods.connect(gui.BLUR, time_changed, b_byoyomi_periods,
                                      3, 1, 9999)
            b_byoyomi_seconds.connect(gui.BLUR, time_changed, b_byoyomi_seconds,
                                      30, 1, 9999)
            def byoyomi_switch_changed(switch, byoyomi_label, byoyomi_periods,
                                       byoyomi_periods_label, byoyomi_seconds,
                                       byoyomi_seconds_label):
                val = switch.value
                byoyomi_label.disabled = not val
                byoyomi_periods.disabled = not val
                byoyomi_periods_label.disabled = not val
                byoyomi_seconds.disabled = not val
                byoyomi_seconds_label.disabled = not val
            w_byoyomi_switch.connect(gui.CHANGE, byoyomi_switch_changed,
                                     w_byoyomi_switch,
                                     w_byoyomi_label, w_byoyomi_periods,
                                     w_byoyomi_periods_label, w_byoyomi_seconds,
                                     w_byoyomi_seconds_label)
            b_byoyomi_switch.connect(gui.CHANGE, byoyomi_switch_changed,
                                     b_byoyomi_switch,
                                     b_byoyomi_label, b_byoyomi_periods,
                                     b_byoyomi_periods_label, b_byoyomi_seconds,
                                     b_byoyomi_seconds_label)

            def set_enabled(switch, widget):
                val = switch.value
                widget.disabled = not val
            show_ai_details_switch.connect(gui.CHANGE, set_enabled,
                                           show_ai_details_switch,
                                           show_ai_details_label)

            cancel_button.connect(gui.CLICK, dialog.close)
            def apply_clicked():
                s['w_player'] = f['w_player_group'].value
                s['w_difficulty'] = f['w_diff_slider'].value
                s['w_use_fixed_time'] = f['w_use_fixed_time'].value
                s['w_minutes'] = int(f['w_fixed_minutes'].value)
                s['w_seconds'] = int(f['w_fixed_seconds'].value)
                s['w_use_byoyomi'] = f['w_use_byoyomi'].value
                s['w_byoyomi_periods'] = int(f['w_byoyomi_periods'].value)
                s['w_byoyomi_seconds'] = int(f['w_byoyomi_seconds'].value)

                s['b_player'] = f['b_player_group'].value
                s['b_difficulty'] = f['b_diff_slider'].value
                s['b_use_fixed_time'] = f['b_use_fixed_time'].value
                s['b_minutes'] = int(f['b_fixed_minutes'].value)
                s['b_seconds'] = int(f['b_fixed_seconds'].value)
                s['b_use_byoyomi'] = f['b_use_byoyomi'].value
                s['b_byoyomi_periods'] = int(f['b_byoyomi_periods'].value)
                s['b_byoyomi_seconds'] = int(f['b_byoyomi_seconds'].value)

                s['territory_marking'] = f['territory_group'].value
                s['show_ai_details'] = f['show_ai_details'].value

                dialog.close()

            apply_button.connect(gui.CLICK, apply_clicked)

            gui.Dialog.__init__(self, title, c)

    class ConfirmDialog(gui.Dialog):
        def __init__(self, title='Confirm', msg='Are you sure?', confirm='OK',
                     confirm_func=None, cancel='Cancel', **kwargs):
            title_lbl = gui.Label(title)

            t = gui.Table()

            t.tr()
            t.add(gui.Label(msg),colspan=2)

            t.tr()
            if confirm_func == None:
                # Just a confirm button.
                e = gui.Button(confirm)
                e.connect(gui.CLICK, self.close, None)
                t.td(e, colspan=2)
            else:
                # Add a confirm and cancel button.
                self.confirm_func = confirm_func

                e = gui.Button(confirm)
                e.connect(gui.CLICK, self.on_confirm, None)
                t.td(e)

                e = gui.Button(cancel)
                e.connect(gui.CLICK, self.close, None)
                t.td(e)

            gui.Dialog.__init__(self, title_lbl, t)

        def on_confirm(self, *args):
            self.close()
            self.confirm_func()

    class RulesDialog(gui.Dialog):
        pass

    class ConnectToRemoteDialog(gui.Dialog):
        def __init__(self, runner):
            self.runner = runner
            title_lbl = gui.Label("Connect to remote player")

            t = gui.Table()

            t.tr()
            t.add(gui.Label("Remote player hostname/IP  "),colspan=2)
            self.w_remote_host = gui.TextArea(value="127.0.0.1",
                                           size=2, width=100, height=20,
                                           name='w_remote_host')
            t.add(self.w_remote_host)
            t.tr()
            t.add(gui.Label("Remote player port  "),colspan=2)
            self.w_remote_port = gui.TextArea(value="60987",
                                           size=2, width=100, height=20,
                                           name='w_remote_port')
            t.add(self.w_remote_port)
            t.tr()
            
            
            e = gui.Button("Cancel")
            e.connect(gui.CLICK, self.close, None)
            t.td(e, colspan=2)

            e = gui.Button("Start")
            e.connect(gui.CLICK, self.start_remote_game, None)
            t.td(e, colspan=2)

            gui.Dialog.__init__(self, title_lbl, t)

        def start_remote_game(self, *args):
            remote_host = self.w_remote_host.value.lstrip().rstrip()
            try:
                remote_port = int(self.w_remote_port.value.lstrip().rstrip())
                if remote_port < 0: raise ValueError
                
            except ValueError:
                class BadPortDialog(gui.Dialog):
                    def __init__(self, *args):
                        title = gui.Label("Port invalid")
                        label = gui.Label("The port number is invalid")
                        gui.Dialog.__init__(self, title, label)
                bpd = BadPortDialog()
                bpd.open()
                return
            self.runner.on_new_game()
            self.runner.white_player = NetworkPlayer(WHITE,
                                              server=remote_host,
                                              port=remote_port)
            self.close()

    class HostRemoteDialog(gui.Dialog):
        def __init__(self, runner):
            self.runner = runner
            title_lbl = gui.Label("Host a remote player")

            t = gui.Table()

            t.tr()
            try:
                addr = socket.gethostbyname(socket.getfqdn())
            except socket.gaierror:
                addr = "unknown"
            t.add(gui.Label("Hosting on hostname/IP  %s" % addr )
                  ,colspan=2)

            t.tr()
            t.add(gui.Label("Use port  "),colspan=2)
            self.w_remote_port = gui.TextArea(value="60987",
                                           size=2, width=100, height=20,
                                           name='w_remote_port')
            t.add(self.w_remote_port)
            t.tr()
            
            
            e = gui.Button("Cancel")
            e.connect(gui.CLICK, self.close, None)
            t.td(e, colspan=2)

            e = gui.Button("Start")
            e.connect(gui.CLICK, self.start_remote_game, None)
            t.td(e, colspan=2)

            gui.Dialog.__init__(self, title_lbl, t)

        def start_remote_game(self, *args):
            remote_port = int(self.w_remote_port.value.lstrip().rstrip())
            self.runner.on_new_game()
            self.runner.black_player = GameHostPlayer(BLACK, port=remote_port)
            
    # UTILITY METHODS #########################################################

    def get_board_x(self):
        board_w = self.surfaces['board'].get_width()
        return ((self.screen_w / 2) - (board_w / 2)) - self.world_x

    def get_board_y(self):
        board_h = self.surfaces['board'].get_height()
        return (self.screen_h + ((self.screen_h / 2) - (board_h / 2))) - self.world_y

    def get_board_w(self):
        return self.surfaces['board'].get_width()

    def get_board_h(self):
        return self.surfaces['board'].get_height()

    def get_screen_pos(self, board_col, board_row):
        """
        Converts board position (square column (x) and row (y)) to the screen
        pixel coordinates of the upper left pixel of the specified square.
        """
        board_x = self.get_board_x()
        board_y = self.get_board_y()
        board_h = self.surfaces['board'].get_height()

        screen_x = board_x + BORDER_PX + (board_col * SQUARE_PX)
        screen_y = (board_y + board_h - 
                    BORDER_PX - SQUARE_PX -
                    (board_row * SQUARE_PX))

        return (screen_x, screen_y)


    def get_board_pos(self, screen_x, screen_y):
        """
        Converts screen coordinates to a board square (column, row) tuple.
        Returns None if the given coordinates are not on the board.
        """
        board_x = self.get_board_x()
        board_y = self.get_board_y()
        board_w = self.surfaces['board'].get_width()
        board_h = self.surfaces['board'].get_height()
        bottom_square = self.game.board.height - 1
        if (screen_x >= board_x + BORDER_PX and 
            screen_x < board_x + board_w - BORDER_PX and
            screen_y >= board_y + BORDER_PX and
            screen_y < board_y + board_h - BORDER_PX):
            square_x = int((screen_x - (board_x + BORDER_PX)) / SQUARE_PX)
            square_y = int(bottom_square - 
                           ((screen_y - (board_y + BORDER_PX)) / SQUARE_PX))
            return (square_x, square_y)
        else:
            return None

    def get_cursor_square(self):
        """
        Returns the (x, y) or (col, row) square the cursor is hovering over,
        or None if the cursor is not over a square.
        """
        return self.get_board_pos(self.mouse['x'], self.mouse['y'])

    def x_at_time(self, xi, vi, a, t):
        """
        Use 1d kinematics to return current x position given an initial
        position (xi), initial velocity (vi), constant acceleration (a) and the
        amount of time that has passed (t).
        Used for making cool screen sliding effects.
        """
        return xi + (vi * t) + (.5 * a * (t * t))

    def accel_for_slide(self, xi, xf, vi, t_total):
        """
        Return the constant acceleration needed to slide from initial x
        position (xi) to final x position (xf), given initial velocity (vi)
        and the total time desired to complete the slide (t_total).
        """
        return -.5 * ((-xf + xi + (vi * t_total)) / (t_total * t_total))

    def interpolated_x_at_time(self, xi, xf, t_total, t):
        """
        Interpolates the current position in a smooth slide, with acceleration
        and decceleration, given an initial position (xi), final position (xf),
        total time for the slide (t_total) and the amount of time that has
        passed (t).
        """
        if t >= t_total:
            return xf
        xmid = xi + ((xf - xi) / 2.0)
        tmid = float(t_total) / 2.0
        a = self.accel_for_slide(xi, xmid, 0.0, tmid)
        if (t < tmid):
            # Accelerating.
            return self.x_at_time(xi, 0.0, a, t*2.0)
        else:
            # Decelerating.
            t_remaining = t_total - t
            x_at_inverted_time = self.x_at_time(xi, 0.0, a, t_remaining*2.0)
            return xf - x_at_inverted_time
