# Data import/export functions
import numpy as np
from numpy.typing import NDArray
from scipy.io import loadmat
import os
import re
from dataclasses import dataclass
from logger_setup import logger

@dataclass
class dataset:
    path: os.PathLike
    name: str
    channels: list
    units: list
    data: NDArray[np.float64]
    tire_id: str
    rim_width: str
    unit_system: str
    coordinate_system: str


def import_mat(filepath):
    """
    Imports data from a MATLAB .mat file and constructs a dataset object with relevant metadata.

    Parameters:
        filepath (os.PathLike): The path to the .mat file to import.

    Returns:
        dataset: An instance of the dataset class containing:
            - filepath (os.PathLike): The original file path.
            - name (str): The base name of the file without extension.
            - channels (list): List of channel names extracted from the file.
            - units (list): List of units corresponding to each channel.
            - data (np.ndarray): ND array of channel data.
            - tire_id (str): Tire identifier extracted from the file.
            - rim_width (str): Rim width extracted from the tire ID string.
            - unit_system (str): 'USCS' if units are in pounds, otherwise 'Metric'.
            - coordinate_system (str): 'SAE' if coordinate information is not present,
              otherwise the coordinate system from the file.

    Raises:
        KeyError: If required keys are missing in the .mat file.
        AttributeError: If expected attributes are missing or malformed in the .mat file.
        ValueError: If rim width cannot be extracted from the tire ID string.
    """
    try:
        # Load the .mat file
        file_data = loadmat(filepath)
        file_name = filepath.stem

        # Extract channel names and units
        channels = np.concatenate(file_data['channel'][0][0][0][0]).ravel().tolist()
        units = np.concatenate(file_data['channel'][0][0][1][0]).ravel().tolist()

        # Stack channel data into a single array
        data = np.column_stack([file_data[chan] for chan in channels])

        # Extract tire ID and rim width
        tire_info = file_data['tireid'][0].split(',')
        tire_id = tire_info[0]
        rim_width = re.search(r"\d+", tire_info[1]).group()

        # Determine unit system
        unit_system = 'USCS' if 'lb' in units else 'Metric'

        # Determine coordinate system
        coordinate_system = 'SAE' if 'coord' not in file_data.keys() else file_data['coord']
        
        logger.info(f"{file_name} successfully imported.")
    except Exception as e:
        logger.error(f"Error importing .MAT file {e}")
    return dataset(filepath,file_name,channels,units,data,tire_id,rim_width,unit_system,coordinate_system)