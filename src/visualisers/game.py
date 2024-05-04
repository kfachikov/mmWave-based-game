from Tracking import TrackBuffer

from games.breakout.breakout import Breakout
from visualisers.visualiser import Visualiser

class GameVisualiser(Visualiser):
    def __init__(self) -> None:
        self.breakout = Breakout()

    def update(self, trackbuffer: TrackBuffer, **kwargs):
        if trackbuffer.effective_tracks:
            track = trackbuffer.effective_tracks[0]
            if track:
                self.breakout.move(-track.displacement * 100)
                track.displacement = 0