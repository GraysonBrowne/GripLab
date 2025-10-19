# converters/conventions.py
"""Sign convention conversion utilities for GripLab application."""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import replace
from enum import Enum

from utils.logger import logger


class SignConvention(Enum):
    """Supported sign conventions."""

    SAE = "SAE"
    ADAPTED_SAE = "Adapted SAE"
    ISO = "ISO"
    ADAPTED_ISO = "Adapted ISO"


class ConventionConverter:
    """Handles conversion between tire testing sign conventions."""

    # Sign convention multipliers relative to SAE baseline
    SIGN_DEFINITIONS: Dict[str, Dict[str, int]] = {
        # Angle channels
        "IA": {"SAE": 1, "Adapted SAE": 1, "ISO": 1, "Adapted ISO": -1},
        "SA": {"SAE": 1, "Adapted SAE": -1, "ISO": -1, "Adapted ISO": 1},
        # Slip channels
        "SR": {"SAE": 1, "Adapted SAE": 1, "ISO": 1, "Adapted ISO": 1},
        "SL": {"SAE": 1, "Adapted SAE": 1, "ISO": 1, "Adapted ISO": 1},
        # Force channels
        "FX": {"SAE": 1, "Adapted SAE": 1, "ISO": 1, "Adapted ISO": 1},
        "FY": {"SAE": 1, "Adapted SAE": 1, "ISO": -1, "Adapted ISO": -1},
        "FZ": {"SAE": 1, "Adapted SAE": -1, "ISO": -1, "Adapted ISO": -1},
        # Moment channels
        "MX": {"SAE": 1, "Adapted SAE": 1, "ISO": 1, "Adapted ISO": 1},
        "MY": {"SAE": 1, "Adapted SAE": 1, "ISO": -1, "Adapted ISO": -1},
        "MZ": {"SAE": 1, "Adapted SAE": 1, "ISO": -1, "Adapted ISO": -1},
        # Command channels
        "CmdIA": {"SAE": 1, "Adapted SAE": 1, "ISO": 1, "Adapted ISO": -1},
        "CmdSA": {"SAE": 1, "Adapted SAE": -1, "ISO": -1, "Adapted ISO": 1},
        "CmdFZ": {"SAE": 1, "Adapted SAE": -1, "ISO": -1, "Adapted ISO": -1},
    }

    # List of supported conventions
    SUPPORTED_CONVENTIONS = ["SAE", "Adapted SAE", "ISO", "Adapted ISO"]

    @classmethod
    def validate_convention(cls, convention: str) -> bool:
        """Check if a sign convention is valid."""
        return convention in cls.SUPPORTED_CONVENTIONS

    @classmethod
    def get_multiplier(
        cls, channel: str, from_convention: str, to_convention: str
    ) -> int:
        """
        Get the multiplier for converting a channel between conventions.

        Args:
            channel: Channel name
            from_convention: Source sign convention
            to_convention: Target sign convention

        Returns:
            Multiplier (1 or -1) for the conversion
        """
        if from_convention == to_convention:
            return 1

        if channel not in cls.SIGN_DEFINITIONS:
            return 1

        channel_def = cls.SIGN_DEFINITIONS[channel]
        from_sign = channel_def.get(from_convention, 1)
        to_sign = channel_def.get(to_convention, 1)

        # Normalize to SAE then apply target
        # If from_sign = -1 and to_sign = -1, result is 1
        # If from_sign = 1 and to_sign = -1, result is -1
        return to_sign // from_sign if from_sign != 0 else 1

    @classmethod
    def convert_channel_data(
        cls, data: np.ndarray, channel: str, from_convention: str, to_convention: str
    ) -> np.ndarray:
        """
        Convert channel data between sign conventions.

        Args:
            data: Array of channel data
            channel: Channel name
            from_convention: Source convention
            to_convention: Target convention

        Returns:
            Converted data array
        """
        multiplier = cls.get_multiplier(channel, from_convention, to_convention)
        if multiplier == 1:
            return data
        return data * multiplier

    @classmethod
    def convert_dataset_convention(cls, dataset: Any, target_convention: str) -> Any:
        """
        Convert entire dataset to target sign convention.

        Args:
            dataset: Dataset object with sign_convention and channels
            target_convention: Target sign convention name

        Returns:
            New dataset with converted signs
        """
        current_convention = dataset.sign_convention

        # No conversion needed
        if current_convention == target_convention:
            return dataset

        # Validate target convention
        if not cls.validate_convention(target_convention):
            logger.error(f"Invalid target convention: {target_convention}")
            return dataset

        try:
            # Create a copy of the dataset
            result = replace(dataset, data=dataset.data.copy())

            # Convert each channel
            for idx, channel in enumerate(result.channels):
                if channel in cls.SIGN_DEFINITIONS:
                    multiplier = cls.get_multiplier(
                        channel, current_convention, target_convention
                    )
                    if multiplier != 1:
                        result.data[:, idx] *= multiplier

            # Update convention
            result.sign_convention = target_convention

            logger.debug(
                f"Converted dataset from {current_convention} to {target_convention}"
            )
            return result

        except Exception as e:
            logger.error(f"Error converting dataset convention: {e}", exc_info=True)
            return dataset

    @classmethod
    def convert_channel_convention(
        cls,
        channels: List[str],
        data: np.ndarray,
        current_convention: str,
        target_convention: str,
    ) -> np.ndarray:
        """
        Convert data array between sign conventions.

        Args:
            channels: List of channel names
            data: 2D data array (rows=samples, cols=channels)
            current_convention: Current sign convention
            target_convention: Target sign convention

        Returns:
            Converted data array
        """
        # No conversion needed
        if current_convention == target_convention:
            return data

        # Validate conventions
        if not cls.validate_convention(target_convention):
            logger.error(f"Invalid target convention: {target_convention}")
            return data

        if not cls.validate_convention(current_convention):
            logger.error(f"Invalid current convention: {current_convention}")
            return data

        try:
            # Create a copy to avoid modifying original
            result = data.copy()

            # Convert each channel
            for idx, channel in enumerate(channels):
                if channel in cls.SIGN_DEFINITIONS:
                    multiplier = cls.get_multiplier(
                        channel, current_convention, target_convention
                    )
                    if multiplier != 1:
                        result[:, idx] *= multiplier

            return result

        except Exception as e:
            logger.error(f"Error converting channel data: {e}", exc_info=True)
            return data

    @classmethod
    def get_convention_info(cls, convention: str) -> Dict[str, str]:
        """
        Get information about a sign convention.

        Args:
            convention: Sign convention name

        Returns:
            Dictionary with convention information
        """
        info = {
            "SAE": {
                "name": "SAE",
                "description": "SAE J670 standard as supplied from tire test consortium",
                "usage": "Standard for tire testing in North America",
            },
            "Adapted SAE": {
                "name": "Adapted SAE",
                "description": "Modified SAE convention used in Pacejka 2012",
                "usage": "Academic and research applications",
            },
            "ISO": {
                "name": "ISO",
                "description": "ISO 8855 standard used in most commercial simulation tools",
                "usage": "ADAMS, MF-Tyre/MF-Swift, and other commercial tools",
            },
            "Adapted ISO": {
                "name": "Adapted ISO",
                "description": "Modified ISO convention used in Besselink 2000",
                "usage": "Specific academic applications",
            },
        }

        return info.get(
            convention,
            {
                "name": convention,
                "description": "Unknown convention",
                "usage": "Unknown",
            },
        )

    @classmethod
    def get_channel_signs(cls, channel: str) -> Optional[Dict[str, int]]:
        """
        Get sign multipliers for a channel across all conventions.

        Args:
            channel: Channel name

        Returns:
            Dictionary of convention to sign multiplier, or None if channel not found
        """
        return cls.SIGN_DEFINITIONS.get(channel)
