import numpy as np
import constants as const
from filterpy.kalman import KalmanFilter
from typing import List

ACTIVE = 1
INACTIVE = 0


class KalmanState:
    def __init__(self, centroid):
        # No control function
        self.inst = KalmanFilter(
            dim_x=const.MOTION_MODEL.KF_DIM[0],
            dim_z=const.MOTION_MODEL.KF_DIM[1],
        )

        self.inst.F = const.MOTION_MODEL.KF_F(1)
        self.inst.H = const.MOTION_MODEL.KF_H

        # We assume independent noise in the x,y,z variables of equal standard deviations.
        self.inst.Q = const.MOTION_MODEL.KF_Q_DISCR(1)
        self.inst.R = np.eye(const.MOTION_MODEL.KF_DIM[1]) * const.KF_R_STD**2

        # For initial values
        self.inst.x = np.array([const.MOTION_MODEL.STATE_VEC(centroid)]).T
        self.inst.P = np.eye(const.MOTION_MODEL.KF_DIM[0]) * 0.001


class PointCluster:
    def calc_centroid(self, pointcloud):
        return np.mean(pointcloud, axis=0)

    def get_min_max_coords(self, pointcloud):
        min_values = np.min(pointcloud, axis=0)
        max_values = np.max(pointcloud, axis=0)
        return (min_values, max_values)

    def __init__(self, pointcloud: np.array):
        # pointcloud should be an np.array of tuples (x,y,z)
        self.pointcloud = pointcloud
        self.point_num = pointcloud.shape[0]
        self.centroid = self.calc_centroid(pointcloud)
        (self.min_vals, self.max_vals) = self.get_min_max_coords(pointcloud)


class ClusterTrack:
    def __init__(self, cluster: PointCluster):
        self.id = None
        # Number of previously estimated points
        self.N_est = 0
        self.spread_est = np.zeros(const.MOTION_MODEL.KF_DIM[1])
        self.group_disp_est = np.eye(const.MOTION_MODEL.KF_DIM[1]) * 0.001
        self.cluster = cluster
        self.state = KalmanState(cluster.centroid)
        self.status = ACTIVE
        self.lifetime = 0
        self.undetected_dt = 0
        self.color = np.random.rand(
            3,
        )
        # NOTE: For visualizing purposes only
        self.predict_x = self.state.inst.x

    def predict_state(self, dt_multiplier):
        self.state.inst.predict(
            F=const.MOTION_MODEL.KF_F(dt_multiplier),
            Q=const.MOTION_MODEL.KF_Q_DISCR(dt_multiplier),
        )
        self.predict_x = self.state.inst.x

    def _estimate_point_num(self):
        if const.KF_ENABLE_EST:
            if self.cluster.point_num > self.N_est:
                self.N_est = self.cluster.point_num
            else:
                self.N_est = (
                    1 - const.KF_A_N
                ) * self.N_est + const.KF_A_N * self.cluster.point_num
        else:
            self.N_est = max(const.KF_EST_POINTNUM, self.cluster.point_num)

    def _estimate_measurement_spread(self):
        for m in range(len(self.cluster.min_vals)):
            spread = self.cluster.max_vals[m] - self.cluster.min_vals[m]

            # Unbiased spread estimation
            if self.cluster.point_num != 1:
                spread = (
                    spread * (self.cluster.point_num + 1) / (self.cluster.point_num - 1)
                )

            # Ensure the computed spread estimation is between 1x and 2x of configured limits
            spread = min(2 * const.KF_SPREAD_LIM[m], spread)
            spread = max(const.KF_SPREAD_LIM[m], spread)

            if spread > self.spread_est[m]:
                self.spread_est[m] = spread
            else:
                self.spread_est[m] = (1.0 - const.KF_A_SPR) * self.spread_est[
                    m
                ] + const.KF_A_SPR * spread

    def _estimate_group_disp_matrix(self):
        a = self.cluster.point_num / self.N_est
        self.group_disp_est = (1 - a) * self.group_disp_est + a * self.get_D()

    def associate_pointcloud(self, pointcloud: np.array):
        self.cluster = PointCluster(pointcloud)
        self._estimate_point_num()
        self._estimate_measurement_spread()
        self._estimate_group_disp_matrix()

    def get_Rm(self):
        rm = np.diag(((self.spread_est / 2) ** 2))
        return rm

    def get_Rc(self):
        N = self.cluster.point_num
        N_est = self.N_est
        return (self.get_Rm() / N) + (
            (N_est - N) / ((N_est - 1) * N)
        ) * self.group_disp_est

    def get_D(self):
        dimension = const.MOTION_MODEL.KF_DIM[1]
        pointcloud = self.cluster.pointcloud
        centroid = self.cluster.centroid
        disp = np.zeros((dimension, dimension), dtype="float")

        for i in range(dimension):
            for j in range(dimension):
                disp[i, j] = np.mean(
                    (pointcloud[:, i] - centroid[i]) * (pointcloud[:, j] - centroid[j])
                )

        return disp

    def update_state(self):
        self.state.inst.update(np.array(self.cluster.centroid), R=self.get_Rc())


class TrackBuffer:
    def __init__(self):
        self.tracks: List[ClusterTrack] = []
        self.effective_tracks: List[ClusterTrack] = []

        # This field keeps track of the iterations that passed until we have valid measurements
        self.dt_multiplier = 1

    def update_status(self):
        for track in self.effective_tracks:
            if track.lifetime > const.TR_LIFETIME:
                track.status = INACTIVE

        # Update effective tracks
        self.effective_tracks = [
            track for track in self.tracks if track.status == ACTIVE
        ]

    def has_active_tracks(self):
        if len(self.effective_tracks) != 0:
            return True
        else:
            return False

    def _calc_dist_fun(self, full_set: np.array):
        dist_matrix = np.empty((full_set.shape[0], len(self.tracks)))
        simple_approach = np.full(full_set.shape[0], None, dtype=object)

        for track in self.effective_tracks:
            j = track.id
            # Find group residual covariance matrix
            H_i = np.dot(const.MOTION_MODEL.KF_H, track.state.inst.x).flatten()

            # TODO: This is probably wrong. Fix it
            # C_g_j = np.dot(np.dot(H_i, track.state.inst.P), H_i.T) + track.get_Rm
            C_g_j = track.state.inst.P[:6, :6] + track.get_Rm() + track.group_disp_est

            for i, point in enumerate(full_set):
                # Find innovation for each measurement
                y_ij = np.array(point) - H_i

                # Find distance function (d^2)
                dist_matrix[i][j] = np.log(np.abs(np.linalg.det(C_g_j))) + np.dot(
                    np.dot(y_ij.T, np.linalg.inv(C_g_j)), y_ij
                )

                # Perform G threshold check
                if dist_matrix[i][j] < const.TR_GATE:
                    # Just choose the closest mahalanobis distance
                    if simple_approach[i] is None:
                        simple_approach[i] = j
                    else:
                        if dist_matrix[i][j] < dist_matrix[i][int(simple_approach[i])]:
                            simple_approach[i] = j

        # return dist_matrix
        return simple_approach

    def add_tracks(self, new_clusters):
        for new_cluster in new_clusters:
            new_track = ClusterTrack(PointCluster(np.array(new_cluster)))
            new_track.id = len(self.tracks)

            self.tracks.append(new_track)
            self.effective_tracks.append(new_track)

    def predict_all(self):
        for track in self.effective_tracks:
            track.predict_state(track.undetected_dt + self.dt_multiplier)

    def update_all(self):
        for track in self.effective_tracks:
            track.update_state()

    def associate_points_to_tracks(self, full_set: np.array):
        unassigned = np.empty((0, const.MOTION_MODEL.KF_DIM[1]), dtype="float")
        clusters = [[] for _ in range(len(self.effective_tracks))]
        simple_matrix = self._calc_dist_fun(full_set)

        for i, point in enumerate(full_set):
            if simple_matrix[i] is None:
                unassigned = np.append(unassigned, [point], axis=0)
            else:
                list_index = None
                for index, track in enumerate(self.effective_tracks):
                    if track.id == simple_matrix[i]:
                        list_index = index
                        break

                clusters[list_index].append(point)

        # TODO: Check for minimum number of points before associating to a track

        for j, track in enumerate(self.effective_tracks):
            if len(clusters[j]) == 0:
                track.lifetime += 1
                track.undetected_dt += self.dt_multiplier
            else:
                track.lifetime = 0
                track.undetected_dt = 0
                track.associate_pointcloud(np.array(clusters[j]))

        return unassigned
