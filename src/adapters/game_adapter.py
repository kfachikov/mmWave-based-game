from Tracking import TrackBuffer

from games.breakout.breakout import Breakout
from adapters.adapter import Adapter

class GameAdapter(Adapter):
    def __init__(self) -> None:
        self.breakout = Breakout()

    def update(self, trackbuffer: TrackBuffer, **kwargs):
        if trackbuffer.effective_tracks:
            track = trackbuffer.effective_tracks[0]
            if track:
                self.breakout.move(-track.displacement * 200)
                track.displacement = 0