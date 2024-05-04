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
        self.width = const.SCREEN_WIDTH // const.COL_NUM # fill the entire screen horizontally
        self.height = 0.5 * const.SCREEN_HEIGHT // const.ROW_NUM # fill only half of the screen vertically

    def initialise_wall(self):
        self.blocks = []
        for row in range(const.ROW_NUM):
            block_row = []
            for col in range(const.COL_NUM):
                # generate x and y positions for each block and create a rectangle from that
                block_x = col * self.width
                block_y = row * self.height
                rect = pygame.Rect(block_x, block_y, self.width, self.height)

                # assign a strength value to each block based on its row
                if row < 2:
                    strength = 3
                elif row < 4:
                    strength = 2
                elif row < 6:
                    strength = 1

                block_individual = [rect, strength]

                block_row.append(block_individual)    
            self.blocks.append(block_row)

    def update_wall(self):
        for row in self.blocks:
            for block in row:
                # assign a color based on block strength
                if block[1] == 3:
                    block_col = const.COLOR_BLOCK_BLUE
                elif block[1] == 2:
                    block_col = const.COLOR_BLOCK_GREEN
                elif block[1] == 1:
                    block_col = const.COLOR_BLOCK_RED
                pygame.draw.rect(self.screen, block_col, block[0])
                pygame.draw.rect(self.screen, const.COLOR_BACKGROUND, (block[0]), 2)
