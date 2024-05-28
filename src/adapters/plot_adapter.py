import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import constants as const

from Tracking import TrackBuffer
from adapters.adapter import Adapter

class PlotAdapter(Adapter):
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

    def __init__(self, raw_cloud=True, b_boxes=True):
        self.dynamic_art = []
        self.arrows = []
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
            plots_index += 1

        plt.show(block=False)

    def update(self, trackbuffer: TrackBuffer, **kwargs):
            if "detObj" not in kwargs:
                raise ValueError("detObj not found in kwargs")
            
            detObj = kwargs["detObj"]

            if detObj is None:
                return

            self.clear()
            self.update_raw(detObj["x"], detObj["y"], detObj["z"])
            self.update_bb(trackbuffer)
            self.draw()

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

        # Remove arrows
        for arrow in self.arrows:
            arrow.remove()
        self.arrows = []

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

            # Draw an arrow in the velocity direction
            # Calculated using the track.state.x[3:6] values
            self.arrows.append(self.ax_bb.quiver(
                track.state.x[0],
                track.state.x[1],
                track.state.x[2],
                track.state.x[3],
                track.state.x[4],
                track.state.x[5],
                color=track.color,
            ))


        # Update 3d plot
        self.bb_scatter = self.ax_bb.scatter(
            x_all, y_all, z_all, c=color_all, marker="o"
        )

    def draw(self):
        plt.draw()
        plt.pause(0.1)  # Pause for a short time to allow for updating