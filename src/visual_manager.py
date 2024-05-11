import constants as const

from adapters.game_adapter import GameAdapter
from adapters.plot_adapter import PlotAdapter
from adapters.screen_adapter import ScreenAdapter

class VisualManager:
    def __init__(self):
        if const.SCREEN_CONNECTED:
            self.visual = ScreenAdapter()
        elif const.GAME:
            self.visual = GameAdapter()
        else:
            self.visual = PlotAdapter()

    def update(self, trackbuffer, detObj=None):
        self.visual.update(trackbuffer, detObj=detObj)