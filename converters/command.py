# converters/command.py
"""Command channel generation for tire test data."""

import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum

from utils.logger import logger
from core.processing import low_pass_filter
from converters.conventions import ConventionConverter


class CommandChannel(Enum):
    """Command channels that can be generated."""

    VELOCITY = "V"
    PRESSURE = "P"
    NORMAL_FORCE = "FZ"
    INCLINATION_ANGLE = "IA"
    SLIP_ANGLE = "SA"


class CmdChannelGenerator:
    """Generates command channels for tire test data analysis."""

    # Target values for command channels by unit system
    CMD_TARGETS: Dict[str, Dict[str, List[float]]] = {
        "V": {"USCS": [0, 2, 15, 25, 45], "Metric": [0, 3, 24, 40, 72]},
        "P": {"USCS": [0, 8, 10, 12, 14], "Metric": [0, 55, 69, 83, 97]},
        "FZ": {
            "USCS": [0, -50, -100, -150, -200, -250, -350],
            "Metric": [0, -222, -445, -667, -890, -1112, -1557],
        },
        "IA": {"USCS": [0, 2, 4], "Metric": [0, 2, 4]},
        "SA": {"USCS": [0, -1, -3, -6, 1, 6], "Metric": [0, -1, -3, -6, 1, 6]},
    }

    # Filtering parameters for noisy channels
    FILTER_CONFIG = {"FZ": {"cutoff_hz": 1, "fs": 100, "order": 2}}

    @classmethod
    def create_cmd_channels(
        cls,
        channels: List[str],
        units: List[str],
        data: np.ndarray,
        unit_system: str,
        sign_convention: str,
    ) -> Tuple[List[str], List[str], np.ndarray]:
        """
        Create command channels for standard test parameters.

        Command channels discretize continuous data into standard test values,
        making it easier to filter and analyze specific test conditions.

        Args:
            channels: List of existing channel names
            units: List of units for each channel
            data: 2D array of channel data
            unit_system: Unit system ('USCS' or 'Metric')
            sign_convention: Sign convention for the data

        Returns:
            Tuple of (updated_channels, updated_units, updated_data)
        """
        # Check if command channels already exist
        existing_cmd_channels = cls._get_existing_cmd_channels(channels)
        if len(existing_cmd_channels) == len(cls.CMD_TARGETS):
            logger.info("All command channels already exist")
            return (channels, units, data)

        # Validate inputs
        if not cls._validate_inputs(channels, units, data, unit_system):
            return (channels, units, data)

        try:
            # Convert to SAE for consistent processing
            data_sae = ConventionConverter.convert_channel_convention(
                channels, data, sign_convention, target_convention="SAE"
            )

            # Generate new command channels
            new_channels, new_units, new_data = cls._generate_cmd_channels(
                channels, units, data_sae, unit_system, existing_cmd_channels
            )

            # Update dataset if new channels were created
            if new_channels:
                channels = channels + new_channels
                units = units + new_units
                data_sae = np.column_stack([data_sae] + new_data)

                logger.info(
                    f"Created {len(new_channels)} command channels: "
                    f"{', '.join(new_channels)}"
                )

            # Convert back to original sign convention
            result_data = ConventionConverter.convert_channel_convention(
                channels,
                data_sae,
                current_convention="SAE",
                target_convention=sign_convention,
            )

            return (channels, units, result_data)

        except Exception as e:
            logger.error(f"Error creating command channels: {e}", exc_info=True)
            return (channels, units, data)

    @classmethod
    def _get_existing_cmd_channels(cls, channels: List[str]) -> List[str]:
        """Get list of command channels that already exist."""
        existing = []
        for chan in cls.CMD_TARGETS.keys():
            if f"Cmd{chan}" in channels:
                existing.append(f"Cmd{chan}")
        return existing

    @classmethod
    def _validate_inputs(
        cls, channels: List[str], units: List[str], data: np.ndarray, unit_system: str
    ) -> bool:
        """Validate input parameters."""
        if len(channels) != len(units):
            logger.error("Channels and units length mismatch")
            return False

        if len(channels) != data.shape[1]:
            logger.error("Channels and data columns mismatch")
            return False

        if unit_system not in ["USCS", "Metric"]:
            logger.error(f"Unsupported unit system: {unit_system}")
            return False

        return True

    @classmethod
    def _generate_cmd_channels(
        cls,
        channels: List[str],
        units: List[str],
        data: np.ndarray,
        unit_system: str,
        existing: List[str],
    ) -> Tuple[List[str], List[str], List[np.ndarray]]:
        """Generate new command channels."""
        new_channels = []
        new_units = []
        new_data = []

        for chan_name, targets in cls.CMD_TARGETS.items():
            cmd_name = f"Cmd{chan_name}"

            # Skip if already exists
            if cmd_name in existing:
                continue

            # Skip if source channel doesn't exist
            if chan_name not in channels:
                logger.warning(
                    f"Source channel {chan_name} not found, skipping {cmd_name}"
                )
                continue

            # Get target values for this unit system
            if unit_system not in targets:
                logger.warning(f"No targets defined for {chan_name} in {unit_system}")
                continue

            # Generate command channel data
            col_idx = channels.index(chan_name)
            cmd_data = cls._discretize_channel(
                data[:, col_idx], targets[unit_system], chan_name
            )

            # Add to results
            new_channels.append(cmd_name)
            new_units.append(units[col_idx])
            new_data.append(cmd_data)

        return new_channels, new_units, new_data

    @classmethod
    def _discretize_channel(
        cls, values: np.ndarray, targets: List[float], channel_name: str
    ) -> np.ndarray:
        """
        Discretize continuous channel data to nearest target values.

        Args:
            values: Continuous channel data
            targets: List of target values
            channel_name: Name of the channel (for filtering decision)

        Returns:
            Discretized data array
        """
        # Apply filtering if configured for this channel
        if channel_name in cls.FILTER_CONFIG:
            config = cls.FILTER_CONFIG[channel_name]
            values = low_pass_filter(values, **config)

        # Convert targets to numpy array for efficient computation
        target_arr = np.array(targets)

        # Find nearest target for each value
        # Uses broadcasting to compute all distances at once
        distances = np.abs(values[:, None] - target_arr)
        nearest_indices = distances.argmin(axis=1)
        nearest_values = target_arr[nearest_indices]

        return nearest_values

    @classmethod
    def get_cmd_channel_info(cls, channel: str, unit_system: str) -> Optional[Dict]:
        """
        Get information about a command channel.

        Args:
            channel: Command channel name (e.g., 'CmdFZ')
            unit_system: Unit system to get targets for

        Returns:
            Dictionary with channel information or None
        """
        # Remove 'Cmd' prefix if present
        base_channel = (
            channel.replace("Cmd", "") if channel.startswith("Cmd") else channel
        )

        if base_channel not in cls.CMD_TARGETS:
            return None

        targets = cls.CMD_TARGETS[base_channel].get(unit_system, [])

        return {
            "channel": f"Cmd{base_channel}",
            "source": base_channel,
            "targets": targets,
            "unit_system": unit_system,
            "filtered": base_channel in cls.FILTER_CONFIG,
        }

    @classmethod
    def validate_cmd_channels(
        cls, channels: List[str], data: np.ndarray
    ) -> Dict[str, bool]:
        """
        Validate that command channels contain expected discrete values.

        Args:
            channels: List of channel names
            data: Channel data array

        Returns:
            Dictionary mapping command channel names to validation status
        """
        validation = {}

        for idx, channel in enumerate(channels):
            if not channel.startswith("Cmd"):
                continue

            unique_values = np.unique(data[:, idx])

            # Check if values are reasonably discrete (not too many unique values)
            is_discrete = len(unique_values) < 20

            validation[channel] = is_discrete

            if not is_discrete:
                logger.warning(
                    f"Command channel {channel} has {len(unique_values)} unique values, "
                    f"expected discrete values"
                )

        return validation
