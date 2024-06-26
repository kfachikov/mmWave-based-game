# Real-time mmWave-based interactive video game

The system is specifically designed to receive radar data from the **IWR1443** millimeter-wave sensor by Texas Instruments (using [IWR1443-Python-API](https://github.com/FmmW-Group/IWR1443-Python-API)).

The **breakout** game is inspired by and built upon [this implementation](https://github.com/MatthewTamYT/Breakout).  

## About

This is the repository for my BSc thesis: 
[*Tracking People for mmWave-based Interactive Game*](http://resolver.tudelft.nl/uuid:cd643124-30d3-45bc-8e3f-020cfc3dd64c)

## Getting Started

### Installation and Execution


1. Clone this repository.
   ```sh
   git clone git@github.com:kfachikov/mmWave-based-game.git
   ```

2. Install Dependencies.
   ```sh
   pip install -r requirements.txt
   ```

3. Adjust the system and scene configurations in `./src/constants.py`. \
Change `P_CLI_PORT` and `P_DATA_PORT` according to your system - use `COM*` on Windows or `/dev/ttyACM*` on Linux.

4. (Optional) For creating\logging an experiment for offline experimentation, run the logging module.
    ```sh
    python3 ./src/DataLogging.py
    ```

5. Run the program online or offline on a logged experiment (specifying its path in `./src/offline_main.py`).
    ```sh
    # online
    python3 ./src/main.py

    # offline
    python3 ./src/offline_main.py
    ```

