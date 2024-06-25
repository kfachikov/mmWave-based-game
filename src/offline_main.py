import sys
import os
from PyQt5.QtWidgets import QApplication
import pygame
from wakepy import keep
import constants as const
from visual_manager import VisualManager
from Utils import OfflineManager, normalize_data
from Tracking import (
    TrackBuffer,
    BatchedData,
)

import time

########### Set the experiment path here ############

EXPERIMENT_PATH = "./dataset/log/mmWave/moving-wide-0.8-1.8"

#####################################################


def offline_main():
    experiment_path = EXPERIMENT_PATH
    if not os.path.exists(experiment_path):
        raise ValueError(f"No experiment file found in the path: {experiment_path}")

    sensor_data = OfflineManager(experiment_path)

    app = QApplication(sys.argv)

    visual = VisualManager()

    trackbuffer = TrackBuffer()
    batch = BatchedData()
    first_iter = True

    # Disable screen sleep/screensaver
    with keep.presenting():
        # Control loop
        while not sensor_data.is_finished():
            t0 = time.time()
            try:
                dataOk, _, detObj = sensor_data.get_data()
                if dataOk:
                    if first_iter:
                        trackbuffer.dt = const.SLEEPTIME
                        first_iter = False
                    else:
                        trackbuffer.dt = detObj["posix"][0] / 1000 - trackbuffer.t

                    trackbuffer.t = detObj["posix"][0] / 1000
                    # Apply scene constraints, translation and static clutter removal
                    effective_data = normalize_data(detObj)

                    if effective_data.shape[0] != 0:
                        # Tracking module
                        trackbuffer.track(effective_data, batch)

                    visual.update(trackbuffer, sensor_data.frame_count, detObj)
                else:
                    visual.update(trackbuffer, sensor_data.frame_count)

            except KeyboardInterrupt:
                break
            finally:
                t_code = time.time() - t0
                t_sleep = max(0, const.SLEEPTIME / const.REFRESH_RATE_COEF - t_code)
                time.sleep(t_sleep)

    pygame.quit()

offline_main()
