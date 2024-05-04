import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Patch

import constants as const
from Tracking import TrackBuffer, ClusterTrack
from Utils import calc_projection_points


def calc_fade_square(track: ClusterTrack):
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

class VisualManager:
    def __init__(self):
        self.mode = const.SCREEN_CONNECTED
        if self.mode:
            self.visual = ScreenAdapter()
        else:
            self.visual = Visualizer(raw_cloud=True, b_boxes=True)

    def update(self, trackbuffer, detObj):
        if const.SCREEN_CONNECTED:
            self.visual.update(trackbuffer)
        else:
            self.visual.clear()
            self.visual.update_raw(detObj["x"], detObj["y"], detObj["z"])
            self.visual.update_bb(trackbuffer)
            self.visual.draw()

class Visualizer:
    def setup_subplot(self, subplot: Axes3D):
        axis_dim = const.V_3D_AXIS
        subplot.set_xlim(axis_dim[0][0], axis_dim[0][1])
        subplot.set_ylim(axis_dim[1][0], axis_dim[1][1])
        subplot.set_zlim(axis_dim[2][0], axis_dim[2][1])
        subplot.set_xlabel("X")
        subplot.set_ylabel("Y")
        subplot.set_zlabel("Z")
        subplot.invert_yaxis()
        subplot.invert_xaxis()
        return subplot.scatter([], [], [])

    def __init__(self, raw_cloud=False, b_boxes=False):
        self.dynamic_art = []
        fig = plt.figure()
        plots_num = sum([raw_cloud, b_boxes])
        plots_index = 1

        if raw_cloud:
            self.ax_raw = fig.add_subplot(1, plots_num, plots_index, projection="3d")
            self.raw_scatter = self.setup_subplot(self.ax_raw)
            self.ax_raw.set_title("Scatter plot of raw Point Cloud")
            plots_index += 1

        if b_boxes:
            # Create subplot of tracks and predictions
            self.ax_bb = fig.add_subplot(1, plots_num, plots_index, projection="3d")
            self.setup_subplot(self.ax_bb)
            self.bb_scatter = None
            self.ax_bb.set_title("Target Tracking")
            # legend_handles = [
            #     Patch(color="red", label="Motion Model Prediction"),
            #     Patch(color="green", label="Pointcloud's Position"),
            #     Patch(color="blue", label="Kalman Filter Output"),
            # ]
            # self.ax_bb.legend(handles=legend_handles)
            plots_index += 1

        plt.show(block=False)

    def clear(self):
        if not hasattr(self, "ax_bb"):
            return

        # Remove pointcloud
        if self.bb_scatter is not None:
            self.bb_scatter.remove()

        # Remove bounding boxes
        for collection in self.dynamic_art:
            collection.remove()
        self.dynamic_art = []

        # Remove screen fading
        for patch in self.ax_bb.patches:
            patch.remove()

    def update_raw(self, x, y, z):
        if not hasattr(self, "ax_raw"):
            return

        # Update the data in the 3D scatter plot
        self.raw_scatter._offsets3d = (x, y, z)
        plt.draw()

    def _draw_bounding_box(self, x, color="gray", fill=0):
        # Create Bounding Boxes
        c = np.array(
            [
                x[0],
                x[1],
                x[2] * 0.0,
            ]
        ).flatten()
        vertices = np.array(
            [
                [-0.3, -0.3, 0],
                [0.3, -0.3, 0],
                [0.3, 0.3, 0],
                [-0.3, 0.3, 0],
                [-0.3, -0.3, 2.5],
                [0.3, -0.3, 2.5],
                [0.3, 0.3, 2.5],
                [-0.3, 0.3, 2.5],
            ]
        )
        vertices = vertices + c
        # vertices = vertices * (const.V_BBOX_HEIGHT / 6) + c
        # Define the cube faces
        faces = [
            [vertices[j] for j in [0, 1, 2, 3]],
            [vertices[j] for j in [4, 5, 6, 7]],
            [vertices[j] for j in [0, 3, 7, 4]],
            [vertices[j] for j in [1, 2, 6, 5]],
            [vertices[j] for j in [0, 1, 5, 4]],
            [vertices[j] for j in [2, 3, 7, 6]],
        ]

        cube = Poly3DCollection(faces, color=[color], alpha=fill)
        self.ax_bb.add_collection3d(cube)
        return cube

    def update_bb(self, trackbuffer: TrackBuffer):
        if not hasattr(self, "ax_bb"):
            return

        x_all = np.array([])  # Initialize as empty NumPy arrays
        y_all = np.array([])
        z_all = np.array([])
        color_all = np.array([]).reshape(0, 3)

        for track in trackbuffer.effective_tracks:
            # We want to visualize only new points.
            # if track.lifetime == 0:
            coords = track.batch.effective_data
            x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]

            # Update pointclouds with different colors for different clusters
            x_all = np.concatenate([x_all, x])
            y_all = np.concatenate([y_all, y])
            z_all = np.concatenate([z_all, z])
            color_all = np.concatenate(
                [color_all, np.repeat([track.color], len(x), axis=0)]
            )

            self.dynamic_art.append(
                self._draw_bounding_box(track.state.x, color=track.color, fill=0.2)
            )

        # Update 3d plot
        self.bb_scatter = self.ax_bb.scatter(
            x_all, y_all, z_all, c=color_all, marker="o"
        )
        # self.ax_bb.set_title(
        #     f"Tracks Number: {len(trackbuffer.effective_tracks)}", loc="left"
        # )

    def draw(self):
        plt.draw()
        plt.pause(0.1)  # Pause for a short time to allow for updating

class ScreenAdapter:
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

    def update(self, trackbuffer: TrackBuffer):
        # Clear previous items in the view
        self.scatter.clear()
        for track in trackbuffer.effective_tracks:
            center, rect_size = calc_fade_square(track)

            self.scatter.addPoints(
                x=center[0] - rect_size / 2,
                y=center[1] - rect_size / 2,
                size=rect_size * self.PIX_TO_M,
            )

        # Update the view
        QApplication.processEvents()
