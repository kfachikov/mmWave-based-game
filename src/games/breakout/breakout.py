import pygame
from pygame.locals import *

import games.breakout.constants as const

from games.breakout.wall import Wall
from games.breakout.paddle import Paddle
from games.breakout.ball import Ball

class Breakout:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((const.SCREEN_WIDTH, const.SCREEN_HEIGHT))
        pygame.display.set_caption('Breakout')

        self.font = pygame.font.SysFont('Constantia', 30)

        self.clock = pygame.time.Clock()
        self.live_ball = False
        self.game_over = 0

        self.wall = Wall(self.screen)
        self.wall.initialise_wall()

        self.player_paddle = Paddle(self.screen)

        self.ball = Ball(self.screen, self.player_paddle.x + (self.player_paddle.width // 2), self.player_paddle.y)

    def _draw_text(self, text, font, color_text, x, y):
        img = font.render(text, True, color_text)
        self.screen.blit(img, (x, y))

    def move(self, paddle_displacement):
        self.clock.tick(const.FPS)

        self.screen.fill(const.COLOR_BACKGROUND)

        self.wall.update_wall()
        self.player_paddle.draw()
        self.ball.draw()

        if self.live_ball:
            self.player_paddle.move(displacement=paddle_displacement)
            self.game_over = self.ball.move(self.wall, self.player_paddle)
            # if self.game_over != 0:
            #     self.live_ball = False

        # print player instructions
        if not self.live_ball:
            if self.game_over == 0:
                self._draw_text('CLICK ANYWHERE TO START', self.font, const.COLOR_TEXT, 100, const.SCREEN_HEIGHT // 2 + 100)
            elif self.game_over == 1:
                self._draw_text('YOU WON!', self.font, const.COLOR_TEXT, 240, const.SCREEN_HEIGHT // 2 + 50)
                self._draw_text('CLICK ANYWHERE TO START', self.font, const.COLOR_TEXT, 100, const.SCREEN_HEIGHT // 2 + 100)
            elif self.game_over == -1:
                self._draw_text('YOU LOST!', self.font, const.COLOR_TEXT, 240, const.SCREEN_HEIGHT // 2 + 50)
                self._draw_text('CLICK ANYWHERE TO START', self.font, const.COLOR_TEXT, 100, const.SCREEN_HEIGHT // 2 + 100)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN and self.live_ball == False:
                self.live_ball = True
                self.ball.reset(self.player_paddle.x + (self.player_paddle.width // 2), self.player_paddle.y - self.player_paddle.height)
                self.player_paddle.reset()
                self.wall.initialise_wall()

        pygame.display.update()

    def run(self):
        run = True
        while run:
            self.clock.tick(const.FPS)

            self.screen.fill(const.COLOR_BACKGROUND)

            self.wall.update_wall()
            self.player_paddle.draw()
            self.ball.draw()

            if self.live_ball:
                # draw paddle
                self.player_paddle.move()
                # draw ball
                self.game_over = self.ball.move(self.wall, self.player_paddle)
                if self.game_over != 0:
                    self.live_ball = False

            # print player instructions
            if not self.live_ball:
                if self.game_over == 0:
                    self._draw_text('CLICK ANYWHERE TO START', self.font, const.COLOR_TEXT, 100, const.SCREEN_HEIGHT // 2 + 100)
                elif self.game_over == 1:
                    self._draw_text('YOU WON!', self.font, const.COLOR_TEXT, 240, const.SCREEN_HEIGHT // 2 + 50)
                    self._draw_text('CLICK ANYWHERE TO START', self.font, const.COLOR_TEXT, 100, const.SCREEN_HEIGHT // 2 + 100)
                elif self.game_over == -1:
                    self._draw_text('YOU LOST!', self.font, const.COLOR_TEXT, 240, const.SCREEN_HEIGHT // 2 + 50)
                    self._draw_text('CLICK ANYWHERE TO START', self.font, const.COLOR_TEXT, 100, const.SCREEN_HEIGHT // 2 + 100)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.MOUSEBUTTONDOWN and self.live_ball == False:
                    self.live_ball = True
                    self.ball.reset(self.player_paddle.x + (self.player_paddle.width // 2), self.player_paddle.y - self.player_paddle.height)
                    self.player_paddle.reset()
                    self.wall.initialise_wall()

            pygame.display.update()

        pygame.quit()