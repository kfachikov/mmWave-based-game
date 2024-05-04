import constants as const

from visualisers.game import GameVisualiser
from visualisers.plot import PlotVisualiser
from visualisers.screen import ScreenVisualiser

class VisualManager:
    def __init__(self):
        if const.SCREEN_CONNECTED:
            self.visual = ScreenVisualiser()
        elif const.GAME:
            self.visual = GameVisualiser()
        else:
            self.visual = PlotVisualiser()

    def update(self, trackbuffer, detObj=None):
        if const.SCREEN_CONNECTED:
            self.visual.update(trackbuffer)
        elif const.GAME:
            self.visual.update(trackbuffer)
        else:
            self.visual.update(trackbuffer, detObj=detObj)