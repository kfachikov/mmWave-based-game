from numpy import dot
from Tracking import Status, TrackBuffer

from games.breakout.breakout import Breakout
from adapters.adapter import Adapter

import constants as const
import games.breakout.constants as game_const 

class GameAdapter(Adapter):
    def __init__(self) -> None:
        self.current_player_pos = 0
        self.breakout = Breakout()
        self.breakout.start()

    def update(self, trackbuffer: TrackBuffer, **kwargs):
        if trackbuffer.effective_tracks:
            track = trackbuffer.effective_tracks[0]
            if track:
                new_player_pos = track.state.x[0]

                displacement_meters = new_player_pos - self.current_player_pos

                # In case the player is moving, but we are inbetween frames, we need to interpolate.
                if displacement_meters == 0 and track.track_status == Status.DYNAMIC:
                    # Interpolate based on predicted position.
                    x = track.state.x
                    F = const.MOTION_MODEL.KF_F(trackbuffer.dt / const.REFRESH_RATE_COEF)
                    new_player_pos = dot(F, x)
                    new_player_pos = new_player_pos[0]

                    displacement_meters = new_player_pos - self.current_player_pos

                displacement_ratio = displacement_meters / const.PLAYGROUND_WIDTH

                displacement_pixels = displacement_ratio * game_const.SCREEN_WIDTH

                self.breakout.move(displacement_pixels)
                
                self.current_player_pos = new_player_pos
            else:
                self.breakout.move(0)
        else: 
            self.breakout.move(0)