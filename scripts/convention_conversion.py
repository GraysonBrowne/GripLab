# scripts/convention_conversion.py
import numpy as np
from dataclasses import replace
from .logger_setup import logger

class ConventionConverter:
    # Sign convention definitions for various channels relative to SAE
    definitions = {
        "IA": {"SAE": 1, "AdaptedSAE":  1, "ISO":  1, "AdaptedISO": -1},
        "SA": {"SAE": 1, "AdaptedSAE": -1, "ISO": -1, "AdaptedISO":  1},
        "SR": {"SAE": 1, "AdaptedSAE":  1, "ISO":  1, "AdaptedISO":  1},
        "SL": {"SAE": 1, "AdaptedSAE":  1, "ISO":  1, "AdaptedISO":  1},
        "FX": {"SAE": 1, "AdaptedSAE":  1, "ISO":  1, "AdaptedISO":  1},
        "FY": {"SAE": 1, "AdaptedSAE":  1, "ISO": -1, "AdaptedISO": -1},
        "FZ": {"SAE": 1, "AdaptedSAE": -1, "ISO": -1, "AdaptedISO": -1},
        "MX": {"SAE": 1, "AdaptedSAE":  1, "ISO":  1, "AdaptedISO":  1},
        "MY": {"SAE": 1, "AdaptedSAE":  1, "ISO": -1, "AdaptedISO": -1},
        "MZ": {"SAE": 1, "AdaptedSAE":  1, "ISO": -1, "AdaptedISO": -1},

        "CmdIA": {"SAE": 1, "AdaptedSAE":  1, "ISO":  1, "AdaptedISO": -1},
        "CmdSA": {"SAE": 1, "AdaptedSAE": -1, "ISO": -1, "AdaptedISO":  1},
        "CmdFZ": {"SAE": 1, "AdaptedSAE": -1, "ISO": -1, "AdaptedISO": -1},
    }

    # List of supported target conventions
    SUPPORTED = set(next(iter(definitions.values())).keys())

    @classmethod
    def convert_dataset_convention(cls, dataset, target_convention: str):
        """
        Converts the sign convention of a dataset to a specified target convention.
        Parameters:
            dataset: An object representing the dataset to be converted.
            target_convention (str): The desired sign convention to convert the 
                dataset to.
        Returns:
            A copy of the input dataset with its data converted to the target 
                sign convention.
        Raises:
            ValueError: If the target convention is not supported.
        Notes:
            - The conversion is performed channel-wise using definitions 
                provided in 'cls.definitions'.
            - Channels not present in 'cls.definitions' are skipped.
            - The function logs the conversion process for debugging purposes.
        """
        try:
            # No conversion needed
            if dataset.sign_convention == target_convention:
                return dataset
            
            # Validate target convention
            if target_convention not in cls.SUPPORTED:
                raise ValueError(f"Unsupported target convention: {target_convention}")

            # Create a copy of the dataset to avoid modifying the original
            result = replace(dataset, data=dataset.data.copy())

            # Convert each channel as needed
            for idx, channel in enumerate(result.channels):
                if channel not in cls.definitions:
                    continue
                
                # Get current and target multipliers
                current = cls.definitions[channel][result.sign_convention]
                target = cls.definitions[channel][target_convention]

                # normalize to SAE, then apply target
                values_sae = result.data[:, idx] / current
                result.data[:, idx] = values_sae * target
        
            logger.debug(f"Converted {dataset.name} from {result.sign_convention} → {target_convention}")
            
            # Update dataset metadata
            result.sign_convention = target_convention
            return result
        except Exception as e:
            logger.error(f"Error converting dataset convention: {e}")
            return dataset          
    
    @classmethod
    def convert_channel_convention(cls, channels: list, data: np.ndarray, 
                                   current_convention: str, target_convention: str):
        """
        Converts the data in a NumPy array from one channel convention to another.
        Parameters:
            channels (list): List of channel names corresponding to the columns 
                in the data array.
            data (np.ndarray): The data array to be converted. Each column 
                corresponds to a channel.
            current_convention (str): The current convention of the data 
                (e.g., 'SAE', 'ISO').
            target_convention (str): The target convention to which the data 
                should be converted.
        Returns:
            np.ndarray: The converted data array with values in the target 
                convention. If an error occurs or no conversion is needed, 
                returns the original data array.
        Raises:
            ValueError: If the target convention is not supported.
        Notes:
            - Channels not found in `cls.definitions` are skipped.
            - The method logs errors and returns the original data in case of exceptions.
        """
        try:
            # No conversion needed
            if current_convention == target_convention:
                return data
            
            # Validate target convention
            if target_convention not in cls.SUPPORTED:
                raise ValueError(f"Unsupported target convention: {target_convention}")

            # Create a copy of the dataset to avoid modifying the original
            result = data.copy()

            # Convert each channel as needed
            for idx, channel in enumerate(channels):
                if channel not in cls.definitions:
                    continue
                
                # Get current and target multipliers
                current = cls.definitions[channel][current_convention]
                target = cls.definitions[channel][target_convention]

                # normalize to SAE, then apply target
                values_sae = result.data[:, idx] / current
                result.data[:, idx] = values_sae * target
        
            return result
        except Exception as e:
            logger.error(f"Error converting data convention: {e}")
            return data      