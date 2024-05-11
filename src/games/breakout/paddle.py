import pygame
from pygame.locals import Rect

import games.breakout.constants as const

class Paddle():
    """
    A class representing the player's paddle.

    Attributes
    ----------
    screen : Surface
        The game screen.
    width : int
        The width of the paddle.
    height : int
        The height of the paddle.
    speed : int
        The speed at which the paddle moves.
    x : int
        The x-coordinate of the paddle.
    y : int
        The y-coordinate of the paddle.
    direction : int
        The direction in which the paddle is moving (-1 for left, 1 for right, 0 for no movement)

    Methods
    -------
    move()
        Moves the paddle based on the player's input.
    draw()
        Draws the paddle on the screen.
    reset()
        Resets the paddle to its initial position. Centered at the bottom of the screen.
    """
    def __init__(self, screen):
        self.screen = screen
        self.width = int(const.SCREEN_WIDTH / const.COL_NUM * const.PADDLE_WIDTH_COEF) # the paddle is as wide as a block
        self.height = int(0.5 * const.SCREEN_HEIGHT / const.ROW_NUM * const.PADDLE_HEIGHT_COEF)
        
        self.speed = const.PADDLE_SPEED
        
        self.reset()

    def move(self):
        self.direction = 0
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
            self.direction = -1
        if key[pygame.K_RIGHT] and self.rect.right < const.SCREEN_WIDTH:
            self.rect.x += self.speed
            self.direction = 1

    def move(self, displacement):
        self.direction = 0
        displacement = -displacement
        if displacement < 0:
            displacement = - min(abs(displacement), self.rect.x)
        else:
            displacement = min(displacement, const.SCREEN_WIDTH - (self.rect.x + self.width))
        self.rect.x += displacement
        self.direction = -1 if displacement < 0 else 1

    def draw(self):
        pygame.draw.rect(self.screen, const.PADDLE_COLOR_FILL, self.rect)
        pygame.draw.rect(self.screen, const.PADDLE_COLOR_OUTLINE, self.rect, 3)

    def reset(self):
        self.x = int((const.SCREEN_WIDTH / 2) - (self.width / 2))
        self.y = const.SCREEN_HEIGHT - (self.height * 1.5)
        
        self.direction = 0
        
        self.rect = Rect(self.x, self.y, self.width, self.height)
