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
        file = loadmat(filepath)
        name = filepath.stem
        channels = np.concatenate(file['channel'][0][0][0][0]).ravel().tolist()
        units = np.concatenate(file['channel'][0][0][1][0]).ravel().tolist()
        data = np.column_stack([file[chan] for chan in channels])
        tire_id = file['tireid'][0].split(',')[0]
        rim_width = re.search(r"\d+", file['tireid'][0].split(',')[1]).group()
        unit_system = 'USCS' if 'lb' in units else 'Metric'
        coordinate_system = 'SAE' if 'coord' not in file.keys() else file['coord']
        
        logger.info(f"{name} successfully imported.")
    except Exception as e:
        logger.error(f"Error importing .MAT file {e}")
    return dataset(filepath,name,channels,units,data,tire_id,rim_width,unit_system,coordinate_system)