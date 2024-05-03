import sys
import os
from PyQt5.QtWidgets import QApplication
from wakepy import keep
import constants as const
from Visualizer import VisualManager
from Utils import OfflineManager, normalize_data
from keras.models import load_model
from Tracking import (
    TrackBuffer,
    BatchedData,
)

########### Set the experiment path here ############

EXPERIMENT_PATH = "./dataset/log/mmWave/tryout"

#####################################################


def offline_main():
    experiment_path = EXPERIMENT_PATH
    if not os.path.exists(experiment_path):
        raise ValueError(f"No experiment file found in the path: {experiment_path}")

    sensor_data = OfflineManager(experiment_path)
    SLEEPTIME = 0.1  # from radar config "frameCfg"

    app = QApplication(sys.argv)

    visual = VisualManager()

    trackbuffer = TrackBuffer()
    batch = BatchedData()
    first_iter = True

    # Disable screen sleep/screensaver
    with keep.presenting():
        # Control loop
        while not sensor_data.is_finished():
            try:
                dataOk, _, detObj = sensor_data.get_data()

                if dataOk:
                    if first_iter:
                        trackbuffer.dt = SLEEPTIME
                        first_iter = False
                    else:
                        trackbuffer.dt = detObj["posix"][0] / 1000 - trackbuffer.t

                    trackbuffer.t = detObj["posix"][0] / 1000
                    # Apply scene constraints, translation and static clutter removal
                    effective_data = normalize_data(detObj)

                    if effective_data.shape[0] != 0:
                        # Tracking module
                        trackbuffer.track(effective_data, batch)

                    visual.update(trackbuffer, detObj)

            except KeyboardInterrupt:
                break


offline_main()
