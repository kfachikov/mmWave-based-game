import numpy as np
import constants as const
import math
import time
from filterpy.kalman import KalmanFilter
from Utils import (
    cluster_pointcloud_dbscan,
    Buffer,
)
from typing import List
from enum import Enum

ACTIVE = 1
INACTIVE = 0

class Status(Enum):
    STATIC = 0,
    DYNAMIC = 1

STATIC = True
DYNAMIC = False


class BatchedData(Buffer):
    """
    A class to manage and combine frames into a batch.

    Attributes:
    ----------
    - effective_data (numpy.ndarray): An array to store effective data frames.

    Methods:
    -------
    - empty(): Reset the buffer and create an empty effective_data array.
    - add_frame(new_data: numpy.ndarray): Add a new frame of data to the buffer.
    - clear(): Clear the buffer and reset effective_data.
    - change_buffer_size(new_size): Change the size of the buffer.
    - pop_frame(): Remove the oldest frame from the buffer.
    """

    def __init__(self):
        super().__init__(const.FB_FRAMES_BATCH + 1, init_val=np.empty((0, 8)))
        self.effective_data = np.empty((0, 8))

    def add_frame(self, new_data: np.array):
        """
        Add a new frame of data to the buffer.
        """
        while len(self.buffer) >= self.size:
            self.pop_frame()

        super().append(new_data)
        self.effective_data = np.concatenate(list(self.buffer), axis=0)

    def clear(self):
        """
        Clear the buffer and reset effective_data.
        """
        self.buffer.clear()
        self.effective_data = np.array([])

    def change_buffer_size(self, new_size):
        """
        Change the size of the buffer.
        """
        self.size = new_size

    def pop_frame(self):
        """
        Remove the oldest frame from the buffer.
        """
        if len(self.buffer) > 0:
            self.buffer.popleft()


class KalmanState(KalmanFilter):
    """
    A class representing the state of a Kalman filter for motion tracking.

    Attributes:
    ----------
    - centroid: The centroid of the track used for initializing this Kalman filter instance.

    Methods:
    -------
    - __init__(centroid: np.ndarray): Initialize the Kalman filter with default parameters based on the centroid.
    """

    def __init__(self, centroid: np.ndarray):
        super().__init__(
            dim_x=const.MOTION_MODEL.KF_DIM[0], dim_z=const.MOTION_MODEL.KF_DIM[1]
        )

        self.F = const.MOTION_MODEL.KF_F(1)
        self.H = const.MOTION_MODEL.KF_H
        self.Q = const.MOTION_MODEL.KF_Q_DISCR(1)
        self.R = np.eye(const.MOTION_MODEL.KF_DIM[1]) * const.KF_R_STD**2
        self.x = np.array([const.MOTION_MODEL.STATE_VEC(centroid)]).T
        self.P = np.eye(const.MOTION_MODEL.KF_DIM[0]) * const.KF_P_INIT


class PointCluster:
    """
    A class representing a cluster of 3D points and its attributes.

    Attributes:
    ----------
    - pointcloud (numpy.ndarray): An array of 3D points in the form (x, y, z, x', y', z', r', s).
    - point_num (int): The number of points in the cluster.
    - centroid (numpy.ndarray): The centroid of the cluster.
    - min_vals (numpy.ndarray): The minimum values in each dimension of the pointcloud.
    - max_vals (numpy.ndarray): The maximum values in each dimension of the pointcloud.
    - status (bool): The cluster movement status (STATIC: True, DYNAMIC: False)

    Methods:
    -------
    - __init__(pointcloud: numpy.ndarray):
        Initialize PointCluster with a given pointcloud.

    """

    def __init__(self, pointcloud: np.array):
        """
        Initialize PointCluster with a given pointcloud.
        """
        self.pointcloud = pointcloud
        self.point_num = pointcloud.shape[0]
        self.centroid = np.mean(pointcloud[:, :6], axis=0)
        self.min_vals = np.min(pointcloud[:, :6], axis=0)
        self.max_vals = np.max(pointcloud[:, :6], axis=0)

        # Check whether the cluster centroid is moving quickly enough or not.
        if math.sqrt(np.sum((self.centroid[3:6] ** 2))) < const.TR_VEL_THRES:
            self.status = STATIC
        else:
            self.status = DYNAMIC


class ClusterTrack:
    """
    A class representing a tracked cluster with a Kalman filter for motion estimation.

    Parameters
    ----------
    cluster : PointCluster
        The initial point cluster associated with the track.

    Attributes
    ----------
    N_est : int
        Estimated number of points in the cluster.
    spread_est : numpy.ndarray
        Estimated spread of measurements in each dimension.
    group_disp_est : numpy.ndarray
        Estimated group dispersion matrix.
    cluster : PointCluster
        PointCluster associated with the track.
    batch : BatchedData
        The collection of overlaying previous frames
    state : KalmanState
        KalmanState instance for motion estimation.
    status : int (INACTIVE or ACTIVE)
        Current status of the track.
    lifetime : int
        Number of frames the track has been active.
    num_points_associated_last : int
        Number of points associated with the track in the last frame.
    num_dynamic_points_associated_last : int
        Number of dynamic points associated with the track in the last frame.
    track_status : Status
        The status of the track (STATIC or DYNAMIC).
    color : numpy.ndarray
        Random color assigned to the track for visualization (for visualization purposes).

    Methods
    -------
    compute_cartesian_velocity()
        Compute the cartesian velocity of the track using the a priori state, with respect to the x and y dimensions.
    
    __get_num_dynamic_points_associated(pointcloud)
        Get the number of dynamic points associated with the track.

    predict_state(dt)
        Predict the state of the Kalman filter based on the time multiplier.

    _estimate_point_num()
        Estimate the number of points in the cluster.

    _estimate_measurement_spread()
        Estimate the spread of measurements in each dimension.

    _estimate_group_disp_matrix()
        Estimate the group dispersion matrix.

    _get_D()
        Calculate and get the dispersion matrix for the track.

    associate_pointcloud(pointcloud)
        Associate a new pointcloud with the track.

    get_Rm()
        Get the measurement covariance matrix.

    _get_Rc()
        Get the combined covariance matrix.

    update_state()
        Update the state of the Kalman filter based on the associated pointcloud.

    update_lifetime(reset=False)
        Update the track lifetime.

    seek_inner_clusters()
        Seek inner clusters within the current track.

    """

    def __init__(self, cluster: PointCluster):
        self.N_est = 0
        self.spread_est = np.zeros(const.MOTION_MODEL.KF_DIM[1])
        self.group_disp_est = (
            np.eye(const.MOTION_MODEL.KF_DIM[1]) * const.KF_GROUP_DISP_EST_INIT
        )
        self.cluster = cluster
        self.batch = BatchedData()
        self.state = KalmanState(cluster.centroid)
        self.status = ACTIVE
        self.lifetime = 0

        self.num_points_associated_last = cluster.point_num
        self.num_dynamic_points_associated_last = self._get_num_dynamic_points_associated(cluster.pointcloud)

        self.track_status = Status.DYNAMIC if self.num_dynamic_points_associated_last > const.NUM_DYNAMIC_POINTS_THRESHOLD else Status.STATIC

        self.color = np.random.rand(
            3,
        )
        
    def compute_cartesian_velocity(self):
        """
        Compute the cartesian velocity of the track using the a priory state, with respect to the x and y dimensions.
        """
        return math.sqrt(np.sum((self.state.x_prior[3:5] ** 2)))
    
    def _get_num_dynamic_points_associated(self, pointcloud: np.array):
        """
        Get the number of dynamic points associated with the track.

        A point is considered dynamic if its Doppler value is greater than the DOPPLER_THRESHOLD.
        """
        return 0 if not len(pointcloud) else np.sum(pointcloud[:, 6] > const.DOPPLER_THRESHOLD)

    def _estimate_point_num(self):
        """
        Estimate the expected number of points in the cluster.
        """
        if const.KF_ENABLE_EST:
            # TODO: Instead of self.cluster.point_num, use my_good_points
            if self.cluster.point_num > self.N_est:
                self.N_est = self.cluster.point_num
            else:
                # Weighted average between the current number of points and the estimated number of points
                self.N_est = (
                    1 - const.KF_A_N
                ) * self.N_est + const.KF_A_N * self.cluster.point_num
        else:
            self.N_est = max(const.KF_EST_POINTNUM, self.cluster.point_num)

    def _estimate_measurement_spread(self):
        """
        Estimate the spread of measurements in each dimension.
        """
        if self.cluster.point_num > 1:
            for m in range(len(self.cluster.min_vals)):
                # Difference between max and min values in the cluster (in one dimension)
                spread = self.cluster.max_vals[m] - self.cluster.min_vals[m]

                # Unbiased spread estimation - the more points we have, the tighter the spread we create is
                spread = (
                    # TODO: Use my_good_points instead of self.cluster.point_num
                    spread * (self.cluster.point_num + 1) / (self.cluster.point_num - 1)
                )

                # Map the spread to a range between 1 and 2 times between the configured spread limits
                spread = min(2 * const.KF_SPREAD_LIM[m], spread)
                spread = max(const.KF_SPREAD_LIM[m], spread)

                if spread > self.spread_est[m]:
                    # This would most likely be the case when we have few samples
                    self.spread_est[m] = spread
                else:
                    # Weighed average between calculated spread and the previous spread estimation
                    self.spread_est[m] = (1.0 - const.KF_A_SPR) * self.spread_est[
                        m
                    ] + const.KF_A_SPR * spread

    def _get_D(self):
        """
        Calculate and get the dispersion matrix for the current cluster.

        Returns
        -------
        numpy.ndarray
            Dispersion matrix for the cluster.
        """
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

    def _estimate_group_disp_matrix(self):
        """
        Estimate the group dispersion matrix.
        """
        a = self.cluster.point_num / self.N_est
        self.group_disp_est = (1 - a) * self.group_disp_est + a * self._get_D()

    def _get_Rc(self):
        """
        Get the combined covariance matrix.

        Returns
        -------
        numpy.ndarray
            Combined covariance matrix for the cluster.
        """
        N = self.cluster.point_num
        N_est = self.N_est
        return (self.get_Rm() / N) + (
            (N_est - N) / ((N_est - 1) * N)
        ) * self.group_disp_est

    def associate_pointcloud(self, pointcloud: np.array):
        """
        Associate a point cloud with the track.

        Parameters
        ----------
        pointcloud : np.array
            2D NumPy array representing the point cloud.

        Notes
        -----
        This method performs the following steps:
        1. Updates the number of points associated with the track.
        2. Updates the number of dynamic points associated with the track.
        3. In case there are point associated with this track, perform the other steps.
        4. Initializes a PointCluster with the given point cloud.
        5. Adds the point-cluster to the track's frames batch.
        """

        # Update the number of points and dynamic associated with the track.
        self.num_points_associated_last = len(pointcloud)
        self.num_dynamic_points_associated_last = self._get_num_dynamic_points_associated(pointcloud)

        # If there are points associated with this track, update the track.
        if len(pointcloud):
            self.cluster = PointCluster(pointcloud)
            self.batch.add_frame(self.cluster.pointcloud)

    def get_Rm(self):
        """
        Get the measurement covariance matrix

        Returns
        -------
        numpy.ndarray
            Measurement covariance matrix for the cluster.
        """
        return np.diag(((self.spread_est / 2) ** 2))

    def predict_state(self, dt: float):
        """
        Predict the state of the Kalman filter based on the time multiplier.

        Parameters
        ----------
        dt : float
            Time multiplier for the prediction.
        """
        if self.track_status is Status.DYNAMIC:
            self.state.predict(
                F=const.MOTION_MODEL.KF_F(dt),
                Q=const.MOTION_MODEL.KF_Q_DISCR(dt),
            )
        
    def update_state(self):
        """
        Update the track.
        """
        # TODO: Calculate my_good_points - dynamic (Doppler more than 0) and unique (association with only one track)
        vel = self.compute_cartesian_velocity()
        # print('Velocity -- ', vel)
        if not self.num_points_associated_last:
            if self.track_status is Status.DYNAMIC:
                if vel < const.MIN_VELOCITY_STOP_NO_POINTS:
                    # If the track is dynamic and no points are associated, force zero velocity.
                    # self.state.x_prior[3:5] = 0
                    # If the track is dynamic and no points are associated, transition to STATIC.
                    self.track_status = Status.STATIC
                # TODO: Otherwise force constant velocity model (zero acceleration).
            else:
                # If the track is static and no points are associated, do not update the state.
                return
        elif self.num_dynamic_points_associated_last < const.NUM_DYNAMIC_POINTS_THRESHOLD + 1:
            if self.track_status is Status.STATIC:
                # TODO: Update confidence.
                return
            else:
                if vel < const.MIN_VELOCITY_STOP_NO_DYNAMIC_POINTS:
                    # If the track is dynamic and no dynamic points are associated, force zero velocity.
                    # self.state.x_prior[3:6] = 0
                    # If the track is dynamic and no dynamic points are associated, transition to STATIC.
                    self.track_status = Status.STATIC 
                    # TODO: If there are many STATIC points, increase confidence.
                elif vel < const.MIN_VELOCITY_SLOW_DOWN:
                    # If the track is dynamic and no dynamic points are associated, slow down the velocity.
                    # self.state.x_prior[3:6] *= 0.5
                    pass
                else:
                    # TODO: Increase confidence. 
                    return
        elif self.num_dynamic_points_associated_last > const.NUM_DYNAMIC_POINTS_THRESHOLD:
            self.track_status = Status.DYNAMIC
            z = np.array(self.cluster.centroid)
            self.state.update(z, R=self._get_Rc())

            self._estimate_point_num()
            self._estimate_measurement_spread()
            self._estimate_group_disp_matrix()

            # If the variance between the Kalman State and measured position is above a threshold, update the state.
            variance = z[:1] - self.state.x[:1, 0]
            if abs(variance.any()) > 0.6 and self.lifetime == 0:
                self.state.x[:1, 0] += variance * 0.4

    def update_lifetime(self, dt, reset=False):
        """
        Update the track lifetime.
        """
        if reset:
            self.lifetime = 0
        else:
            self.lifetime += dt

class TrackBuffer:
    """
    A class representing a buffer for managing and updating the multiple ClusterTracks of the scene.

    Attributes
    ----------
    effective_tracks : List[ClusterTrack]
        List of currently active (non-INACTIVE) tracks in the buffer.
    next_track_id : int
        The id int that will be given to the next active track.
    dt : float
        Time multiplier used for predicting states. Indicates the time passed since the previous
        valid observed frame.
    t : float
        Current time when the TrackBuffer is instantiated / updated.

    Methods
    -------
    _maintain_tracks()
        Update the status of tracks based on their lifetime.

    update_ef_tracks()
        Update the list of effective tracks (excluding INACTIVE tracks).

    has_active_tracks()
        Check if there are active tracks in the buffer.

    _calc_dist_fun(full_set)
        Calculate the Mahalanobis distance matrix for gating.

    _add_tracks(new_clusters)
        Add new tracks to the buffer.

    _predict_all()
        Predict the state of all effective tracks.

    _update_all()
        Update the state of all effective tracks.

    _get_gated_clouds(full_set)
        Gate the pointcloud and return gated and unassigned clouds.

    _associate_points_to_tracks(full_set)
        Associate points to existing tracks and handle inner cluster separation.

    track(pointcloud, batch)
        Perform the tracking process including prediction, association, status update, and clustering.

    estimate_posture(model)
        Estimate the posture of each track in the buffer using a CNN model.

    """

    def __init__(self):
        """
        Initialize TrackBuffer with empty lists for tracks and effective tracks.
        """
        self.effective_tracks: List[ClusterTrack] = []
        self.next_track_id = 0
        self.dt = 0
        self.t = time.time()

    def _maintain_tracks(self):
        """
        Update the status of tracks based on their mobility and lifetime. Then update the list of effective tracks.
        """
        for track in self.effective_tracks:
            if track.cluster.status == DYNAMIC:
                lifetime = const.TR_LIFETIME_DYNAMIC
            else:
                lifetime = const.TR_LIFETIME_STATIC

            if track.lifetime > lifetime:
                track.status = INACTIVE

        self.effective_tracks[:] = [
            track for track in self.effective_tracks if track.status != INACTIVE
        ]

    def _find_closest_track(self, full_set: np.array):
        """
        Calculate the Mahalanobis distance matrix for gating.

        Parameters
        ----------
        full_set : np.ndarray
            Full set of points.

        Returns
        -------
        np.ndarray
            An array representing the associated track (entry) for each point (index).
            If no track is associated with a point, the entry is set to None.
        """
        bidding_score = np.empty((full_set.shape[0], len(self.effective_tracks)))
        associated_track_for = np.full(full_set.shape[0], None, dtype=object)

        for j, track in enumerate(self.effective_tracks):
            H_i = np.dot(const.MOTION_MODEL.KF_H, track.state.x_prior).flatten()
            # Group residual covariance matrix
            C_g_j = track.state.P_prior[:6, :6] + track.get_Rm() + track.group_disp_est

            for i, point in enumerate(full_set):
                # Innovation for each measurement
                y_ij = np.array(point[:6]) - H_i

                # Mahalanobis Distance (squared)
                d_squared = np.dot(np.dot(y_ij.T, np.linalg.inv(C_g_j)), y_ij)

                # bidding score (squared)
                bidding_score[i][j] = np.log(np.abs(np.linalg.det(C_g_j))) + d_squared

                # Perform Gate threshold check
                if bidding_score[i][j] < const.TR_GATE:
                    # Just choose the closest mahalanobis distance
                    if associated_track_for[i] is None:
                        associated_track_for[i] = j
                    else:
                        if (
                            bidding_score[i][j]
                            < bidding_score[i][int(associated_track_for[i])]
                        ):
                            associated_track_for[i] = j

        return associated_track_for

    def _add_tracks(self, new_clusters):
        """
        Add new tracks to the buffer.

        Parameters
        ----------
        new_clusters : list
            List of new clusters to be added as tracks.
        """
        for new_cluster in new_clusters:
            new_track = ClusterTrack(PointCluster(np.array(new_cluster)))
            # new_track.id = self.next_track_id
            self.next_track_id += 1
            self.effective_tracks.append(new_track)

    def _predict_all(self):
        """
        Predict the state of all effective tracks.
        """
        for track in self.effective_tracks:
            # TODO: Maybe, accumulate dt for this track in case it is not updated.
            track.predict_state(track.lifetime + self.dt)

    def _update_all(self):
        """
        Update the state of all effective tracks.
        """
        for track in self.effective_tracks:
            # TODO: Update only when the track is active (static or dynamic). Delete FREE tracks.
            track.update_state()

    def _get_gated_clouds(self, full_set: np.array):
        """
        Split the pointcloud according to the formed gates and return gated and unassigned clouds.

        Parameters
        ----------
        full_set : np.array
            Full set of points.

        Returns
        -------
        tuple
            Tuple containing unassigned points and clustered clouds.
        """
        unassigned = np.empty((0, 8), dtype="float")
        clusters = [[] for _ in range(len(self.effective_tracks))]
        # Simple matrix has len = len(full_set) and has the index of the chosen track.
        point_to_closest_track_assignment = self._find_closest_track(full_set)

        for i, point in enumerate(full_set):
            if point_to_closest_track_assignment[i] is None:
                unassigned = np.append(unassigned, [point], axis=0)
            else:
                clusters[point_to_closest_track_assignment[i]].append(point)

        return unassigned, clusters

    def _assign_points_to_tracks_and_get_unassigned(self, full_set: np.array):
        """
        Associate points to existing tracks.

        Parameters
        ----------
        full_set : np.array
            Full set of sensed points.

        Returns
        -------
        np.ndarray
            Unassigned points.
        """
        unassigned, clouds = self._get_gated_clouds(full_set)

        for j, track in enumerate(self.effective_tracks):
            track.update_lifetime(dt=self.dt, reset=not (len(clouds[j]) == 0))
            track.associate_pointcloud(np.array(clouds[j]))

        return unassigned

    def track(self, pointcloud, batch: BatchedData, isBetweenFrame: bool = False):
        """
        Perform the tracking process including prediction, association, maintenance, update, and clustering.

        Parameters
        ----------
        pointcloud : np.array
            Pointcloud data.
        batch : BatchedData
            BatchedData instance for managing frames.

        Returns
        -------
        None
        """
        # Prediction Step
        self._predict_all()

        # Association Step
        unassigned = self._assign_points_to_tracks_and_get_unassigned(pointcloud)

        # Update Step
        self._update_all()

        # TODO: Move Allocation step before maintenance.

        # Maintenance Step
        # self._maintain_tracks()

        # Clustering of the remainder points Step
        new_clusters = []
        batch.add_frame(unassigned)

        if (
            len(batch.effective_data) > 0
            and len(self.effective_tracks) < const.TR_MAX_TRACKS
        ):
            new_clusters = cluster_pointcloud_dbscan(batch.effective_data)

            if len(new_clusters) > 0:
                batch.clear()

            # Create new track for every new cluster
            self._add_tracks(new_clusters)
