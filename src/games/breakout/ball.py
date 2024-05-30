import pygame
from pygame.locals import Rect

import games.breakout.constants as const

class Ball():
    """
    A class representing the ball in the game.

    Attributes
    ----------
    screen : Surface
        The game screen.
    ball_rad : int
        The radius of the ball.
    speed_max : int
        The maximum speed of the ball.
    x : int
        The x-coordinate of the ball.
    y : int
        The y-coordinate of the ball.
    speed_x : int
        The speed of the ball in the x-direction.
    speed_y : int
        The speed of the ball in the y-direction.
    game_over : int
        The game state (0 for ongoing, 1 for win, -1 for loss).
    rect : Rect
        A rectangle representing the ball.

    Methods
    -------
    move()
        Moves the ball and checks for collisions with the paddle, blocks, and walls.
    draw()
        Draws the ball on the screen.
    reset(x, y)
        Resets the ball to its initial position.
    """
    def __init__(self, screen, x, y, speed_max = 5):
        self.screen = screen
        self.ball_rad = int(0.5 * const.SCREEN_HEIGHT / const.ROW_NUM * const.BALL_SIZE_COEF)
        self.speed_max = speed_max

        self.reset(x, y)

    def move(self, wall, player_paddle):

        # collision threshold
        collision_thresh_x = self.speed_max
        collision_thresh_y = abs(self.speed_y)

        wall_destroyed = 1
        
        for row_idx, row in enumerate(wall.blocks):
            for col_ixd, item in enumerate(row):
                # check whether the ball collides with a block
                if self.rect.colliderect(item[0]):
                    # object above
                    if abs(self.rect.bottom - item[0].top) < collision_thresh_y and self.speed_y > 0:
                        self.speed_y *= -1
                    # object below
                    elif abs(self.rect.top - item[0].bottom) < collision_thresh_y and self.speed_y < 0:
                        self.speed_y *= -1
                    # object on the right
                    elif abs(self.rect.right - item[0].left) < collision_thresh_x and self.speed_x > 0:
                        self.speed_x *= -1
                    # object on the left
                    elif abs(self.rect.left - item[0].right) < collision_thresh_x and self.speed_x < 0:
                        self.speed_x *= -1

                    if wall.blocks[row_idx][col_ixd][1] > 1:
                        wall.blocks[row_idx][col_ixd][1] -= 1
                    else:
                        wall.blocks[row_idx][col_ixd][0] = (0, 0, 0, 0)

                # if a block still exists, the wall is not destroyed
                if wall.blocks[row_idx][col_ixd][0] != (0, 0, 0, 0):
                    wall_destroyed = 0

        if wall_destroyed == 1:
            self.game_over = 1

        if self.rect.left < 0 or self.rect.right > const.SCREEN_WIDTH:
            self.speed_x *= -1

        if self.rect.top < 0:
            self.speed_y *= -1
        if self.rect.bottom > const.SCREEN_HEIGHT:
            self.game_over = -1

        if self.rect.colliderect(player_paddle):
            if abs(self.rect.bottom - player_paddle.rect.top) < collision_thresh_y and self.speed_y > 0:
                self.speed_y *= -1
                self.speed_x += player_paddle.direction # the paddle direction influences the ball's speed
                if self.speed_x > self.speed_max:
                    self.speed_x = self.speed_max
                elif self.speed_x < 0 and self.speed_x < -self.speed_max:
                    self.speed_x = -self.speed_max

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        return self.game_over

    def draw(self):
        self.draw_circle_alpha(self.screen, const.PADDLE_COLOR_FILL, (self.rect.x + self.ball_rad, self.rect.y + self.ball_rad),
                               self.ball_rad)
        
    def draw_circle_alpha(self, surface, color, center, radius):
        target_rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
        shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
        pygame.draw.circle(shape_surf, color, (radius, radius), radius)
        surface.blit(shape_surf, target_rect)

    def reset(self, x, y):
        self.x = x - self.ball_rad
        self.y = y - 2 * self.ball_rad
        
        self.speed_x = int(self.speed_max * const.BALL_SPEED_INITIAL_COEF)
        self.speed_y = -(self.speed_max * const.BALL_SPEED_INITIAL_COEF)

        self.game_over = 0
        
        self.rect = Rect(self.x, self.y, self.ball_rad * 2, self.ball_rad * 2)