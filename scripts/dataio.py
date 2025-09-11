# scripts/dataio.py
import numpy as np
from numpy.typing import NDArray
from scipy.io import loadmat
import os
import re
from itertools import islice
from dataclasses import dataclass, replace
from .logger_setup import logger
from .unit_conversion import UnitSystemConverter
from .cmd_generator import CmdChannelGenerator

@dataclass
class dataset:
    path: os.PathLike
    name: str
    channels: list
    units: list
    unit_types: list
    data: NDArray[np.float64]
    tire_id: str
    rim_width: int
    unit_system: str
    sign_convention: str
    node_color: str
    notes: str
    demo_name: str
    demo_tire_id: str = "Brand, Compound, Size"
    demo_rim_width: int = 0
    demo_notes: str = ""

class DataManager:
    def __init__(self):
        self._datasets = {}  # key: name, value: dataset object

    def add_dataset(self, name, dataset):
        self._datasets[name] = dataset

    def get_dataset(self, name):
        return self._datasets.get(name)

    def list_datasets(self):
        return list(self._datasets.keys())

    def remove_dataset(self, name):
        self._datasets.pop(name, None)

    def get_channels(self, names):
        channels = []
        for name in names:
            dataset = self.get_dataset(name)
            channels.extend(dataset.channels)
        return list(dict.fromkeys(channels))  # Return unique channels
    
    def list_tire_ids(self):
        return [ds.tire_id for ds in self._datasets.values()]

    def list_colors(self):
        return [ds.node_color for ds in self._datasets.values()]
    
    def parse_dataset(self, dataset, channel, condition):
        result = replace(dataset, data=dataset.data.copy())
        ref_channel = result.channels.index(channel)
        ref_array = result.data[:,ref_channel]
        parse_index = np.isin(ref_array, condition)
        result.data = result.data[parse_index,:]
        return result
    
    def update_dataset(self, old_name, new_name):
        updated_dict = {}
        for k, v in self._datasets.items():
            if k == old_name:
                updated_dict[new_name] = self._datasets[old_name]
            else:
                updated_dict[k] = v
        self._datasets = updated_dict

    def list_demo_names(self):
        return [ds.demo_name for ds in self._datasets.values()]

    def update_demo_name(self, old_name, new_name):
        updated_dict = {}
        for k, v in self._datasets.items():
            if k == old_name:
                updated_dict[k] = replace(v, demo_name=new_name)
            else:
                updated_dict[k] = v
        self._datasets = updated_dict

    def list_demo_tire_ids(self):
        return [ds.demo_tire_id for ds in self._datasets.values()]


def import_mat(filepath, file_name, node_color, demo_name):
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
            - unit_types (list): List of unit types corresponding to each channel.
            - data (np.ndarray): 2D array of channel data.
            - tire_id (str): Tire identifier extracted from the file.
            - rim_width (int): Rim width extracted from the tire ID string.
            - unit_system (str): 'USCS' if units are in pounds, otherwise 'Metric'.
            - sign_convention (str): Extracted sign convention, defaults to 'SAE' if not found.
            - node_color (str): Hex code that determines plotting color.
            - notes (str): String of notes associated with the dataset.

    Raises:
        Exception: Logs and handles any errors encountered during file import.
    """
    try:
        # Load the .mat file
        file_data = loadmat(filepath)

        # Extract channel names and units
        channels = np.concatenate(file_data['channel'][0][0][0][0]).ravel().tolist()
        units = np.concatenate(file_data['channel'][0][0][1][0]).ravel().tolist()

        # Stack channel data into a single array
        data = np.column_stack([file_data[chan] for chan in channels])

        # Ensure 'SL' channel exists
        if 'SL' not in channels:
            channels.append('SL')
            units.append('none')
            data = np.column_stack([data,np.zeros(len(data),np.float64)])

        # Extract tire ID and rim width
        tire_info = file_data['tireid'][0].split(',')
        tire_id = tire_info[0]

        rim_match = re.search(r"\d+", tire_info[1])
        rim_width = int(rim_match.group()) if rim_match else 0

        # Determine unit system
        if 'units' in file_data.keys():
            unit_system = file_data['units']
        else:
            unit_system = 'USCS' if 'lb' in units else 'Metric'
            logger.warning(f"No unit system specified in {file_name}, {unit_system} inferred from channel names.")

        # Determine sign convention
        if 'sign' in file_data.keys():
            sign_convention = file_data['sign']
        else:
            sign_convention = 'SAE'
            logger.warning(f"No sign convention specified in {file_name}, defaulting to SAE.")

        # Create command channels if needed
        channels, units, data = CmdChannelGenerator.create_cmd_channels(channels, 
                                                                        units, 
                                                                        data, 
                                                                        unit_system, 
                                                                        sign_convention)
        
        # Map channels to unit types
        unit_types = UnitSystemConverter.map_channels_to_types(channels)

        # Extract notes
        if 'notes' in file_data.keys():
            notes = file_data['notes']
        else:
            notes = ''
            logger.warning(f"Notes string not found in {file_name}.")
        
        logger.info(f"{file_name} successfully imported.")
    except Exception as e:
        logger.error(f"Error importing .MAT file {e}", exc_info=True)
    return (dataset(filepath, file_name, channels, units, unit_types, data,
                   tire_id, rim_width, unit_system, sign_convention, node_color,
                   notes, demo_name))

def import_dat(filepath, file_name, node_color, demo_name):
    """
    Imports data from a .dat/.txt file and constructs a dataset object with relevant metadata.

    Parameters:
        filepath (os.PathLike): Path to the .dat/.txt file to import.

    Returns:
        dataset: An instance of the dataset class containing:
            - filepath (os.PathLike): The original file path.
            - file_name (str): The base name of the file without extension.
            - channels (list): List of channel names.
            - units (list): List of units corresponding to each channel.
            - unit_types (list): List of unit types corresponding to each channel.
            - data (np.ndarray): 2D array of channel data.
            - tire_id (str): Tire identifier extracted from the file.
            - rim_width (int): Rim width extracted from the tire ID string.
            - unit_system (str): 'USCS' if units are in pounds, otherwise 'Metric'.
            - sign_convention (str): Extracted sign convention, defaults to 'SAE' if not found.
            - node_color (str): Hex code that determines plotting color.
            - notes (str): String of notes associated with the dataset.

    Raises:
        Exception: Logs and handles any errors encountered during file import.
    """
    try:
        # Read the first three lines for metadata
        with open(filepath, "r") as f:
            first_three = list(islice(f, 3))

        # Extract channel names and units
        channels = first_three[1].strip().split('\t')
        units = first_three[2].strip().split('\t')

        # Stack channel data into a single array
        data = np.loadtxt(filepath,delimiter='\t',skiprows=3)

        # Ensure 'SL' channel exists
        if 'SL' not in channels:
            channels.append('SL')
            units.append('none')
            data = np.column_stack([data,np.zeros(len(data),np.float64)])

        # Extract tire ID and rim width
        tire_match = re.search(r'Tire_Name=([^;]+)', first_three[0])
        tire_id = tire_match.group(1) if tire_match else ''

        rim_match = re.search(r'Rim_Width=([^;]+)', first_three[0])
        rim_width = int(float(rim_match.group(1))) if rim_match else 0

        # Determine unit system
        unit_match = re.search(r'Unit_System=([^;]+)', first_three[0])
        if unit_match:
            unit_system = unit_match.group(1)
        else:
            unit_system = 'USCS' if 'lb' in units else 'Metric'
            logger.warning(f"No unit system specified in {file_name}, {unit_system} inferred from channel names.")

        # Determine sign convention
        sign_match = re.search(r'Sign_Convention=([^;]+)', first_three[0])
        if sign_match:
            sign_convention = sign_match.group(1)
        else:
            sign_convention = 'SAE'
            logger.warning(f"No sign convention specified in {file_name}, defaulting to SAE.")

        # Create command channels if needed
        channels, units, data = CmdChannelGenerator.create_cmd_channels(channels, 
                                                                        units, 
                                                                        data, 
                                                                        unit_system, 
                                                                        sign_convention)
        
        # Map channels to unit types
        unit_types = UnitSystemConverter.map_channels_to_types(channels)

        # Extract notes
        notes_match = re.search(r'Notes=([^;]+)', first_three[0])
        if notes_match:
            notes = sign_match.group(1)
        else:
            notes = ''
            logger.warning(f"Notes string not found in {file_name}.")
            
        logger.info(f"{file_name} successfully imported.")
    except Exception as e:
        logger.error(f"Error importing .DAT/.TXT file {e}", exc_info=True)
    return (dataset(filepath, file_name, channels, units, unit_types, data,
                   tire_id, rim_width, unit_system, sign_convention, node_color,
                   notes, demo_name))