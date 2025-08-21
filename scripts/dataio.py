# Data import/export functions
import numpy as np
from numpy.typing import NDArray
from scipy.io import loadmat
import os
import re
from itertools import islice
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
            - file_name (str): The base name of the file without extension.
            - channels (list): List of channel names.
            - units (list): List of units corresponding to each channel.
            - data (np.ndarray): 2D array of channel data.
            - tire_id (str): Tire identifier extracted from the file.
            - rim_width (str): Rim width extracted from the tire ID string.
            - unit_system (str): 'USCS' if units are in pounds, otherwise 'Metric'.
            - coordinate_system (str): Extracted coordinate system, defaults to 'SAE' if not found.

    Raises:
        Exception: Logs and handles any errors encountered during file import.
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

        rim_match = re.search(r"\d+", tire_info[1])
        rim_width = rim_match.group() if rim_match else ''

        # Determine unit system
        unit_system = 'USCS' if 'lb' in units else 'Metric'

        # Determine coordinate system
        coordinate_system = 'SAE' if 'coord' not in file_data.keys() else file_data['coord']
        
        logger.info(f"{file_name} successfully imported.")
    except Exception as e:
        logger.error(f"Error importing .MAT file {e}")
    return dataset(filepath,file_name,channels,units,data,tire_id,rim_width,unit_system,coordinate_system)

def import_dat(filepath):
    """
    Imports data from a .dat/.txt file and constructs a dataset object with relevant metadata.

    Parameters:
        filepath (os.PathLike): Path to the .dat/.txt file to import.

    Returns:
        dataset: An instance of the dataset class containing:
            - filepath (os.PathLike): The original file path.
            - file_name (str): The base name of the file without extension.
            - channels (list of str): List of channel names.
            - units (list of str): List of units corresponding to each channel.
            - data (np.ndarray): 2D array of channel data.
            - tire_id (str): Tire identifier extracted from the file.
            - rim_width (str or None): Rim width extracted from the tire ID string.
            - unit_system (str): 'USCS' if units are in pounds, otherwise 'Metric'.
            - coordinate_system (str): Extracted coordinate system, defaults to 'SAE' if not found.

    Raises:
        Exception: Logs and handles any errors encountered during file import.
    """
    try:
        # Load the .dat file
        file_name = filepath.stem

        with open(filepath, "r") as f:
            first_three = list(islice(f, 3))

        # Extract channel names and units
        channels = first_three[1].strip().split('\t')
        units = first_three[2].strip().split('\t')

        # Stack channel data into a single array
        data = np.loadtxt(filepath,delimiter='\t',skiprows=3)

        # Extract tire ID and rim width
        tire_match = re.search(r'Tire_Name=([^;]+)', first_three[0])
        tire_id = tire_match.group(1) if tire_match else ''

        rim_match = re.search(r'Rim_Width=([^;]+)', first_three[0])
        rim_width = str(int(float(rim_match.group(1)))) if rim_match else ''

        # Determine unit system
        unit_system = 'USCS' if 'lb' in units else 'Metric'

        # Determine coordinate system
        coord_match = re.search(r'Coordinate_System=([^;]+)', first_three[0])
        coordinate_system = coord_match.group(1) if coord_match else 'SAE'
            
        
        logger.info(f"{file_name} successfully imported.")
    except Exception as e:
        logger.error(f"Error importing .DAT/.TXT file {e}")
    return dataset(filepath,file_name,channels,units,data,tire_id,rim_width,unit_system,coordinate_system)