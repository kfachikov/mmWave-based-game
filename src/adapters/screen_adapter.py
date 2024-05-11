import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication

import constants as const

from Tracking import TrackBuffer, ClusterTrack
from adapters.adapter import Adapter

from Utils import calc_projection_points


class ScreenAdapter(Adapter):
    def __init__(self):
        self.win = pg.GraphicsLayoutWidget()
        self.view = self.win.addPlot()
        self.view.setAspectLocked()
        self.view.getViewBox().setBackgroundColor((255, 255, 255))
        self.view.setRange(
            xRange=(-const.SCREEN_SIZE[0] / 2, const.SCREEN_SIZE[0] / 2),
            yRange=(const.SCREEN_HEIGHT, const.SCREEN_SIZE[1]),
        )
        self.view.invertX()
        self.win.showMaximized()

        # Create a scatter plot with squares
        brush = pg.mkBrush(color=(0, 0, 0))
        self.scatter = pg.ScatterPlotItem(pen=None, brush=brush, symbol="s")
        self.view.addItem(self.scatter)

        self.PIX_TO_M = 3779 * const.V_SCALLING

    def update(self, trackbuffer: TrackBuffer, **kwargs):
        # Clear previous items in the view
        self.scatter.clear()
        for track in trackbuffer.effective_tracks:
            center, rect_size = self._calc_fade_square(track)

            self.scatter.addPoints(
                x=center[0] - rect_size / 2,
                y=center[1] - rect_size / 2,
                size=rect_size * self.PIX_TO_M,
            )

        # Update the view
        QApplication.processEvents()

    def _calc_fade_square(self, track: ClusterTrack):
        center = calc_projection_points(
            track.state.x[0] + track.keypoints[11],
            track.state.x[1] + track.keypoints[12],
            track.keypoints[13],
        )
        rect_size = max(
            const.V_SCREEN_FADE_SIZE_MIN,
            min(
                const.V_SCREEN_FADE_SIZE_MAX,
                const.V_SCREEN_FADE_SIZE_MAX
                - (track.state.x[1] + track.keypoints[12]) * const.V_SCREEN_FADE_WEIGHT,
            ),
        )
        return (center, rect_size)
