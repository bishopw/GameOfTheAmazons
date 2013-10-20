import os, sys

import pygame
from pygame.locals import *
from pgu import gui

from square import Square
from move import Move
from board import Board
from game import Game

# Useful constants.
SQUARE_PX = 60 # Size of a board square in pixels.
BORDER_PX = 30 # Size of the borders of the board in pixels.

class PygameRunner(object):
    """
    A pygame-based GUI and game controller for Game of the Amazons.

    Pygame app outline originally based on the Pygame Cheat Sheet:
    http://inventwithpython.com/pygamecheatsheet.png
    """

    # Different phases the game app can be in.
    PHASE_TITLE = 0
    PHASE_TRANSITION = 1
    PHASE_GAME = 2

    # Sub-phases.
    SUBPHASE_WAIT_FOR_AI = 0
    SUBPHASE_PICK_AMAZON = 1
    SUBPHASE_PLACE_AMAZON = 2
    SUBPHASE_SHOOT_ARROW = 3

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
        self.white_player = 'Local Human'
        self.black_player = 'Local Human'
        self.clock = 'No Clock'

        s = self.game_settings
        self.game = Game(s['width'], s['height'], s['white_amazons'],
                         s['black_amazons'], s['arrows'], s['to_move'])

        self.phase = self.PHASE_TITLE
        self.subphase = self.SUBPHASE_PICK_AMAZON

        self.amazon_in_hand = None # Amazon currently being held by player.


    # GAME AND APP CONTROL ####################################################
    def run(self):
        """
        Start up the pygame timing and video systems, run the game, then quit
        once the player is done.
        """
        pygame.init()
        self.fpsClock = pygame.time.Clock()

        # Prepare the main window surface that graphics will be rendered to.
        # Make it 80% of the desktop height and width.
        info = pygame.display.Info()
        self.screen_w = int(info.current_w * .8)
        self.screen_h = int(info.current_h * .8)
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
            'freesansbold': pygame.font.Font('freesansbold.ttf', 32)
        }
        self.sounds = {
            'bounce': pygame.mixer.Sound('bounce.wav')
        }

        # Set up the app window.
        pygame.display.set_caption('Game of the Amazons')
        pygame.display.set_icon(self.surfaces['app_icon'])

        # Initialize game state.
        self.msg = 'Hello world!'
        self.mouse = { 'x':0, 'y':0 }
        self.quitting = False
        self.world_x = 0 # Coordinates we are at in the game world.
        self.world_y = 0
        self.movement_vector = { 'x': 0, 'y': 0 } # Camera movement vector.

        # Create and start GUI.
        gui_app = gui.App()

        self.title_gui = self.TitleGUI(runner=self)

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
        sys.exit

    def game_loop(self):
        """Run the main game loop until the player quits."""
        while not self.quitting:
            # Update game state.
            if self.phase == self.PHASE_TRANSITION:
                # Slide to the board or back to the title screen.
                self.world_y = int(self.interpolated_x_at_time(0.0, self.screen_h, 
                                                               15.0,
                                                               float(self.transition_tick)))
                self.transition_tick += 1
                if (self.transition_tick == 15):
                    self.world_y = self.screen_h
                    self.phase = self.PHASE_GAME
                    self.start_current_move()

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

            elif event.type == MOUSEBUTTONUP:
                self.mouse['x'], self.mouse['y'] = event.pos
                self.sounds['bounce'].play()
                if self.subphase == self.SUBPHASE_PICK_AMAZON:
                    self.pick_amazon()
                elif self.subphase == self.SUBPHASE_PLACE_AMAZON:
                    self.place_amazon()
                elif self.subphase == self.SUBPHASE_SHOOT_ARROW:
                    self.shoot_arrow()
                if event.button in (1, 2, 3):
                    self.msg = 'left, middle, or right mouse click'

            elif event.type == KEYUP:
                if event.key == K_ESCAPE:
                    pygame.event.post(pygame.event.Event(QUIT))

    def on_new_game(self):
        s = self.game_settings
        self.game = Game(s['width'], s['height'], s['white_amazons'],
                         s['black_amazons'], s['arrows'], s['to_move'])

        # Update GUI.
        self.gui_cont.remove(self.title_gui)

        # Update Phase.
        self.phase = self.PHASE_TRANSITION
        self.transition_tick = 0

    def start_current_move(self):
        """
        Chooses the appropriate subphase given the current player (human or AI).
        """
        self.amazon_in_hand = None
        self.amazon_target = None
        board = self.game.board
        curr_player = (self.white_player if (board.to_move == "white") 
                       else self.black_player)
        self.subphase = (self.SUBPHASE_PICK_AMAZON
                         if curr_player == 'Local Human'
                         else self.SUBPHASE_WAIT_FOR_AI)

    def pick_amazon(self):
        """Pick the amazon at the current cursor position to move."""
        sq = self.get_cursor_square()
        if sq == None:
            return
        board = self.game.board
        sq = Square(sq)
        if sq in board.current_amazons:
            self.amazon_in_hand = Square(sq)
            self.subphase = self.SUBPHASE_PLACE_AMAZON

    def place_amazon(self):
        """Choose a target square to move the amazon in hand."""
        sq = self.get_cursor_square()
        board = self.game.board
        if sq == None:
            return
        sq = Square(sq)
        if board.is_path_clear(self.amazon_in_hand, sq):
            self.amazon_target = sq
            self.subphase = self.SUBPHASE_SHOOT_ARROW

    def shoot_arrow(self):
        """Choose a target square to shoot an arrow and execute a move."""
        sq = self.get_cursor_square()
        board = self.game.board
        if sq == None:
            return
        sq = Square(sq)
        if board.is_path_clear(self.amazon_target, sq, ignore=self.amazon_in_hand):
            arrow_target = sq
            mv = Move(self.amazon_in_hand, self.amazon_target, arrow_target)
            if board.check_is_move_valid(mv):
                self.game.move(mv)
                self.start_current_move()

    def cancel_move(self):
        """
        Cancels current amazon pick and/or placement and returns to the
        pick amazon subphase.
        """
        self.amazon_in_hand = None
        self.amazon_target = None
        self.subphase = self.SUBPHASE_PICK_AMAZON


    # RENDERING ###############################################################

    def render(self):
        """Render the current game state to screen."""
        window = self.window
        window.fill(self.colors['black'])

        self.render_background()

        self.render_title()

        if self.phase != self.PHASE_TITLE:
            self.render_board()

        if self.phase == self.PHASE_GAME:
            self.render_indicators()

        if self.phase != self.PHASE_TRANSITION:
            self.gui_app.paint()

        self.render_cursor()

        pygame.display.update()

    def render_cursor(self):
        board = self.game.board
        c_surf = self.surfaces['cursor']
        if self.subphase == self.SUBPHASE_PLACE_AMAZON:
            c_surf = (self.surfaces['white_cursor'] if board.to_move == 'white'
                      else self.surfaces['black_cursor'])
        elif self.subphase == self.SUBPHASE_SHOOT_ARROW:
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

        # TODO Draw territory if the option is on.

    def render_indicators(self):
        """
        Draw circles and squares indicating legal/illegal clicks, and hazy_white
        pieces to indicate amazons chosen for movement.
        """
        if self.subphase == self.SUBPHASE_WAIT_FOR_AI:
            return

        # Draw hazy pieces.
        board = self.game.board
        hazy_surf = (self.surfaces['hazy_white'] if board.to_move == "white"
                     else self.surfaces['hazy_black'])

        if (self.subphase == self.SUBPHASE_PLACE_AMAZON
            or self.subphase == self.SUBPHASE_SHOOT_ARROW):
            hazy_x, hazy_y = self.get_screen_pos(self.amazon_in_hand.x,
                                                 self.amazon_in_hand.y)
            self.blit_clipped(hazy_surf, hazy_x, hazy_y)

        if self.subphase == self.SUBPHASE_SHOOT_ARROW:
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
        if self.subphase == self.SUBPHASE_PICK_AMAZON:
            is_legal = c_square in board.current_amazons
        elif self.subphase == self.SUBPHASE_PLACE_AMAZON:
            is_legal = board.is_path_clear(self.amazon_in_hand, c_square)
        elif self.subphase == self.SUBPHASE_SHOOT_ARROW:
            is_legal = board.is_path_clear(self.amazon_target, c_square, 
                                           ignore=self.amazon_in_hand)
        surf = self.surfaces['circle'] if is_legal else self.surfaces['x']
        self.blit_clipped(surf,
                          indicator_pos[0],
                          indicator_pos[1])

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
            e = gui.Button('New Game - Wait for Remote Player')
            self.td(e)
            self.tr()
            e = gui.Button('New Game - Connect to Remote Player')
            self.td(e)
            self.tr()
            e = gui.Button('Options')
            self.td(e)
            self.tr()
            quit_d = PygameRunner.QuitDialog()
            class QuitButton(gui.Button):
                def __init__(self, **kwargs):
                    kwargs['value'] = 'Quit'
                    gui.Button.__init__(self, **kwargs)
                    self.connect(gui.CLICK,quit_d.open,None)
            e = QuitButton()
            self.td(e)

    class QuitDialog(gui.Dialog):
        def __init__(self, **kwargs):
            title = gui.Label('Confirm Quit')

            t = gui.Table()

            t.tr()
            t.add(gui.Label('Are you sure you want to quit?'),colspan=2)

            t.tr()
            e = gui.Button("Quit")
            e.connect(gui.CLICK,self.on_click, None)
            t.td(e)

            e = gui.Button("Cancel")
            e.connect(gui.CLICK, self.close, None)
            t.td(e)

            gui.Dialog.__init__(self, title, t)

        def on_click(self, *args):
            pygame.event.post(pygame.event.Event(QUIT))


    # UTILITY METHODS #########################################################

    def get_board_x(self):
        board_w = self.surfaces['board'].get_width()
        return ((self.screen_w / 2) - (board_w / 2)) - self.world_x

    def get_board_y(self):
        board_h = self.surfaces['board'].get_height()
        return (self.screen_h + ((self.screen_h / 2) - (board_h / 2))) - self.world_y

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