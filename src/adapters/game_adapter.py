from Tracking import TrackBuffer

from games.breakout.breakout import Breakout
from adapters.adapter import Adapter

import constants as const
import games.breakout.constants as game_const 

import os

class GameAdapter(Adapter):
    def __init__(self) -> None:
        # x = 0
        # y = -2160
        # os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"

        self.current_player_pos = 0
        self.breakout = Breakout()
        self.breakout.start()

        if (const.REPORTING_OFFLINE):
            self.player_position = []
            self.paddle_positions = []

    def update(self, trackbuffer: TrackBuffer, **kwargs):
        if trackbuffer.effective_tracks:
            track = trackbuffer.effective_tracks[0]
            if track:
                new_player_pos = track.state.x[0]
                displacement_meters = new_player_pos - self.current_player_pos

                displacement_ratio = displacement_meters / const.PLAYGROUND_WIDTH

                displacement_pixels = displacement_ratio * game_const.SCREEN_WIDTH

                self.breakout.move(displacement_pixels)
                
                self.current_player_pos = new_player_pos

                if (const.REPORTING_OFFLINE):
                    # Condition on the frame num. Necessary due to starting and closing the application.
                    if (kwargs['frame_number'] > 100 and kwargs['frame_number'] < 450):
                        self.player_position.append(self.current_player_pos[0])
                        self.paddle_positions.append(self.breakout.player_paddle.rect.x)
            else:
                self.breakout.move(0)
        else: 
            self.breakout.move(0)