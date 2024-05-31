import pygame

import games.breakout.constants as const

class Wall():
    """
    A class representing the game blocks.

    Attributes
    ----------
    screen : Surface
        The game screen.
    width : int
        The width of each individual block.
    height : int
        The height of each individual block.
    blocks : list
        A two-dimensional list containing the blocks. Each block is represented by a list containing a rectangle and a strength value.
        The strength indicates the number of hits required to destroy that block.

    Methods
    -------
    create_wall()
        Creates the block instances and stores them in the blocks list.
    draw_wall()
        Draws the blocks on the screen. The block color is determined by each block's strength.
    
    """
    def __init__(self, screen):
        self.screen = screen
        self.width = (const.SCREEN_WIDTH - 3) // const.COL_NUM # fill the entire screen horizontally
        self.height = -3 + 0.5 * const.SCREEN_HEIGHT // const.ROW_NUM # fill only half of the screen vertically

    def initialise_wall(self):
        self.blocks = []
        for row in range(const.ROW_NUM):
            block_row = []
            for col in range(const.COL_NUM):
                # generate x and y positions for each block and create a rectangle from that
                block_x = 3 + col * self.width
                block_y = 3 + row * self.height
                rect = pygame.Rect(block_x, block_y, self.width, self.height)

                strength = 1

                block_individual = [rect, strength]

                block_row.append(block_individual)    
            self.blocks.append(block_row)

    def update_wall(self):
        for row in self.blocks:
            for block in row:
                block_col = const.COLOR_BLOCK_DELFT_BLUE
                pygame.draw.rect(self.screen, block_col, block[0])
                pygame.draw.rect(self.screen, (255,255,255), (block[0]), 3)
