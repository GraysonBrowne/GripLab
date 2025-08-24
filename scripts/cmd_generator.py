# scripts/cmd_generator.py
import numpy as np
from logger_setup import logger
from processing import low_pass_filter
from convention_conversion import ConventionConverter

class CmdChannelGenerator:
    # TODO:
    # Confirm these values again once plotting is further along
    # Make a unit conversion method to make the target dict less redundant

    # Target command values for various channels in different unit systems
    cmd_target = {
        'V': {
            'USCS': [0, 2, 15, 25, 45],
            'Metric': [0, 3.2, 24.1, 40.2, 72.4]
        },
        'P': {
            'USCS': [0, 8, 10, 12, 14],
            'Metric': [0, 55.2, 68.9, 82.7, 96.5]
        },
        'FZ': {
            'USCS': [0, -50, -100, -150, -200, -250, -350],
            'Metric': [0, -222.4, -444.8, -667.2, -889.6, -1112.1, -1556.9]
        },
        'IA': {
            'USCS': [0, 2, 4, -4],
            'Metric': [0, 2, 4, -4]
        },
        'SA': {
            'USCS': [0, -1, -3, -6, -12, 1, 6, 12],
            'Metric': [0, -1, -3, -6, -12, 1, 6, 12]
        }
    }

    @classmethod
    def create_cmd_channels(cls, channels: list, units: list, data: np.ndarray, 
                            unit_system: str, sign_convention: str):
        """
        Creates command channels (e.g., CmdFZ, CmdP) based on specified target 
        values for each channel and appends them to the dataset if they do not 
        already exist. This method ensures that command channels are generated 
        according to the specified unit system and sign convention, applying 
        necessary conversions and filtering as needed. For each target channel, 
        it maps the original data to the nearest target value, optionally 
        applying a low-pass filter for specific channels (e.g., FZ) to reduce 
        noise before matching.
        Args:
            channels (list): List of existing channel names.
            units (list): List of units corresponding to each channel.
            data (np.ndarray): 2D array of shape containing the data.
            unit_system (str): The unit system to use for target values (e.g., 'USCS', 'Metric').
            sign_convention (str): The sign convention of the input data (e.g., 'SAE', 'ISO').
        Returns:
            tuple: Updated (channels, units, data) with command channels 
                appended if they were created.
        Raises:
            ValueError: If the specified unit system is not supported for a channel.
            Exception: For any other errors encountered during processing.
        Notes:
            - If command channels already exist in the input, the method returns
                 the original data unchanged.
            - Data is internally converted to the 'SAE' convention for 
                processing and converted back to the original convention if needed.
        """
        try:
            # Check if command channels already exist
            cmd_chans = [f"Cmd{c}" for c in cls.cmd_target.keys()]
            if all(c in channels for c in cmd_chans):
                logger.info("Command channels already exist.")
                return (channels, units, data)

            new_channels, new_units, new_data = [], [], []

            # Convert data to SAE convention for consistent processing
            data_sae = ConventionConverter.convert_channel_convention(channels,
                                                                      data, 
                                                                      sign_convention, 
                                                                      target_convention = 'SAE')
                                                                    
            # Generate command channels
            for chan, targets in cls.cmd_target.items():
                if f"Cmd{chan}" in channels:
                    continue

                if unit_system not in targets:
                    raise ValueError(f"Unsupported unit system {unit_system} for {chan}")

                # Find column index for the channel
                col_idx = channels.index(chan)

                # Get target array for the current unit system
                target_arr = np.array(targets[unit_system])

                # For FZ, apply low-pass filter to reduce noise before matching
                if chan == 'FZ':
                    values = low_pass_filter(data_sae[:, col_idx], cutoff_hz=1, fs=100, order=2)
                else:
                    values = data_sae[:, col_idx]

                # Map each value to the nearest target
                nearest = target_arr[np.abs(values[:, None] - target_arr).argmin(axis=1)]

                # Append new channel info
                new_channels.append(f"Cmd{chan}")
                new_units.append(units[col_idx])
                new_data.append(nearest)

            # Update dataset in-place
            if new_channels:
                channels.extend(new_channels)
                units.extend(new_units)
                data_sae = np.column_stack([data_sae] + new_data)
                logger.info(f"Created {len(new_channels)} command channels: {', '.join(new_channels)}")

            # Convert back to original sign convention if needed
            result = ConventionConverter.convert_channel_convention(channels, 
                                                                    data_sae, 
                                                                    current_convention = 'SAE', 
                                                                    target_convention = sign_convention)

            return (channels, units, result)
        except Exception as e:
            logger.error(f"Error creating command channels: {e}")
            return (channels, units, result)