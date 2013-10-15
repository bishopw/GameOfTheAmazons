import os, sys

import pygame
from pygame.locals import *


class PygameRunner(object):
    """
    A pygame-based GUI and game controller for Game of the Amazons.

    Pygame app outline originally based on the Pygame Cheat Sheet:
    http://inventwithpython.com/pygamecheatsheet.png
    """

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

        pygame.mouse.set_visible(False) # We'll use our custom cursor instead.

        self.game_loop()

        pygame.mouse.set_visible(True)

        pygame.quit()
        sys.exit

    def game_loop(self):
        """Run the main game loop until the player quits."""
        while not self.quitting:
            self.render()

            self.process_inputs()

            self.fpsClock.tick(30)

    def render(self):
        """Render the current game state to screen."""
        window = self.window
        window.fill(self.colors['black'])

        self.render_background()

        self.render_title()

        window.blit(self.surfaces['cursor'], (self.mouse['x'], self.mouse['y']))

        msgSurfaceObj = self.fonts['freesansbold'].render(self.msg, False, self.colors['blue'])
        msgRectobj = msgSurfaceObj.get_rect()
        msgRectobj.topleft = (10, 20)
        window.blit(msgSurfaceObj, msgRectobj)
        pygame.display.update()

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
        x = (window.get_width() / 2) - (t_surf.get_width() / 2)
        y = (window.get_height() / 2) - (t_surf.get_height() / 2)
        self.blit_clipped(t_surf, x, y)

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

    def process_inputs(self):
        """Process player input for one tick of the game."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.quitting = True
            elif event.type == MOUSEMOTION:
                self.mouse['x'], self.mouse['y'] = event.pos
                self.msg = 'Mouse: (' + str(self.mouse['x']) + ', ' + str(self.mouse['y']) + ')'
            elif event.type == MOUSEBUTTONUP:
                self.mouse['x'], self.mouse['y'] = event.pos
                self.sounds['bounce'].play()
                if event.button in (1, 2, 3):
                    self.msg = 'left, middle, or right mouse click'
                elif event.button in (4, 5):
                    self.msg = 'mouse scrolled up or down'

            elif event.type == KEYDOWN:
                if event.key == K_LEFT:
                    self.movement_vector['x'] = -10
                    self.msg = 'left'
                elif event.key == K_RIGHT:
                    self.movement_vector['x'] = 10
                    self.msg = 'right'
                elif event.key == K_UP:
                    self.movement_vector['y'] = -10
                elif event.key == K_DOWN:
                    self.movement_vector['y'] = 10
            elif event.type == KEYUP:
                if event.key in (K_LEFT, K_RIGHT):
                    self.movement_vector['x'] = 0
                elif event.key in (K_UP, K_DOWN):
                    self.movement_vector['y'] = 0
                elif event.key == K_a:
                    self.msg = '"A" key pressed.'
                elif event.key == K_ESCAPE:
                    pygame.event.post(pygame.event.Event(QUIT))

        # Move through the world according to the current movement vector.
        self.world_x += self.movement_vector['x']
        self.world_x = max(0, self.world_x)
        self.world_x = min(3200, self.world_x)
        self.world_y += self.movement_vector['y']
        self.world_y = max(0, self.world_y)
        self.world_y = min(3200, self.world_y)
        self.msg = "world: " + str(self.world_x) + ',' + str(self.world_y)
