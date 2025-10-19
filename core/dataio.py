# core/dataio.py
"""Data I/O and management for GripLab application."""

import os
import re
from dataclasses import dataclass, field, replace
from itertools import islice
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray
from scipy.io import loadmat

from converters.command import CmdChannelGenerator
from converters.units import UnitSystemConverter
from utils.logger import logger


@dataclass
class Dataset:
    """Container for tire test data."""

    # Core data
    path: Path
    name: str
    channels: List[str]
    units: List[str]
    unit_types: List[str]
    data: NDArray[np.float64]

    # Metadata
    tire_id: str
    rim_width: int
    unit_system: str
    sign_convention: str
    node_color: str
    notes: str = ""

    # Demo mode attributes
    demo_name: str = "Demo data"
    demo_tire_id: str = "Brand, Compound, Size"
    demo_rim_width: int = 0
    demo_notes: str = ""

    def __post_init__(self):
        """Validate dataset after initialization."""
        if len(self.channels) != len(self.units):
            raise ValueError("Channels and units must have same length")
        if len(self.channels) != self.data.shape[1]:
            raise ValueError("Number of channels must match data columns")

    def get_channel_data(self, channel: str) -> Optional[NDArray]:
        """Get data for a specific channel."""
        try:
            idx = self.channels.index(channel)
            return self.data[:, idx]
        except ValueError:
            logger.warning(f"Channel {channel} not found in dataset")
            return None

    def get_channel_unit(self, channel: str) -> Optional[str]:
        """Get unit for a specific channel."""
        try:
            idx = self.channels.index(channel)
            return self.units[idx]
        except ValueError:
            return None


class DataManager:
    """Manages collection of datasets with operations."""

    def __init__(self):
        self._datasets: Dict[str, Dataset] = {}

    # ===== Core Operations =====

    def add_dataset(self, name: str, dataset: Dataset) -> bool:
        """Add a dataset to the collection."""
        if name in self._datasets:
            logger.warning(f"Dataset {name} already exists, overwriting")
        self._datasets[name] = dataset
        return True

    def get_dataset(self, name: str) -> Optional[Dataset]:
        """Retrieve a dataset by name."""
        return self._datasets.get(name)

    def remove_dataset(self, name: str) -> bool:
        """Remove a dataset from the collection."""
        if name in self._datasets:
            del self._datasets[name]
            return True
        logger.warning(f"Dataset {name} not found for removal")
        return False

    def list_datasets(self) -> List[str]:
        """Get list of all dataset names."""
        return list(self._datasets.keys())

    # ===== Bulk Operations =====

    def get_channels(self, names: List[str]) -> List[str]:
        """Get unique channels across multiple datasets."""
        channels = []
        for name in names:
            dataset = self.get_dataset(name)
            if dataset:
                channels.extend(dataset.channels)
        # Return unique channels while preserving order
        return list(dict.fromkeys(channels))

    def parse_dataset(
        self, dataset: Dataset, channel: str, condition: List[Any]
    ) -> Optional[Dataset]:
        """Filter dataset based on channel condition."""
        try:
            if channel not in dataset.channels:
                logger.warning(f"Channel {channel} not found for parsing")
                return dataset

            result = replace(dataset, data=dataset.data.copy())
            ref_idx = result.channels.index(channel)
            ref_array = result.data[:, ref_idx].astype(np.int64)
            parse_index = np.isin(ref_array, condition)
            result.data = result.data[parse_index, :]

            return result
        except Exception as e:
            logger.error(f"Error parsing dataset: {e}", exc_info=True)
            return dataset

    # ===== Property Accessors =====

    def list_tire_ids(self) -> List[str]:
        """Get tire IDs from all datasets."""
        return [ds.tire_id for ds in self._datasets.values()]

    def list_colors(self) -> List[str]:
        """Get node colors from all datasets."""
        return [ds.node_color for ds in self._datasets.values()]

    def list_demo_names(self) -> List[str]:
        """Get demo names from all datasets."""
        return [ds.demo_name for ds in self._datasets.values()]

    def list_demo_tire_ids(self) -> List[str]:
        """Get demo tire IDs from all datasets."""
        return [ds.demo_tire_id for ds in self._datasets.values()]

    # ===== Update Operations =====

    def update_dataset(self, old_name: str, new_name: str) -> bool:
        """Rename a dataset in the collection."""
        if old_name not in self._datasets:
            logger.warning(f"Dataset {old_name} not found for update")
            return False

        if old_name != new_name:
            updated_dict = {}
            for k, v in self._datasets.items():
                if k == old_name:
                    updated_dict[new_name] = self._datasets[old_name]
                else:
                    updated_dict[k] = v
            self._datasets = updated_dict
        return True

    def update_demo_name(self, old_name: str, new_name: str) -> bool:
        """Update demo name for a dataset."""
        dataset = None
        for ds in self._datasets.values():
            if ds.demo_name == old_name:
                dataset = ds
                break

        if dataset:
            dataset.demo_name = new_name
            return True

        logger.warning(f"Demo name {old_name} not found for update")
        return False


class DataImporter:
    """Handles importing data from various file formats."""

    @staticmethod
    def import_file(
        filepath: Path, name: str, node_color: str, demo_name: str
    ) -> Optional[Dataset]:
        """Import data file based on extension."""
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return None

        ext = filepath.suffix.lower()

        if ext == ".mat":
            return DataImporter.import_mat(filepath, name, node_color, demo_name)
        elif ext in [".dat", ".txt"]:
            return DataImporter.import_dat(filepath, name, node_color, demo_name)
        else:
            logger.error(f"Unsupported file type: {ext}")
            return None

    @staticmethod
    def import_mat(
        filepath: Path, name: str, node_color: str, demo_name: str
    ) -> Optional[Dataset]:
        """Import MATLAB .mat file."""
        try:
            # Load file
            file_data = loadmat(str(filepath))

            # Extract channels and units
            channels = np.concatenate(file_data["channel"][0][0][0][0]).ravel().tolist()
            units = np.concatenate(file_data["channel"][0][0][1][0]).ravel().tolist()

            # Stack channel data
            data = np.column_stack([file_data[chan] for chan in channels])

            # Ensure SL channel exists
            if "SL" not in channels:
                channels.append("SL")
                units.append("-")
                data = np.column_stack([data, np.zeros(len(data))])

            # Extract metadata
            metadata = DataImporter._extract_mat_metadata(file_data, name)

            # Generate command channels
            channels, units, data = CmdChannelGenerator.create_cmd_channels(
                channels,
                units,
                data,
                metadata["unit_system"],
                metadata["sign_convention"],
            )

            # Map unit types
            unit_types = UnitSystemConverter.map_channels_to_types(channels)

            # Create dataset
            return Dataset(
                path=filepath,
                name=name,
                channels=channels,
                units=units,
                unit_types=unit_types,
                data=data,
                tire_id=metadata["tire_id"],
                rim_width=metadata["rim_width"],
                unit_system=metadata["unit_system"],
                sign_convention=metadata["sign_convention"],
                node_color=node_color,
                notes=metadata["notes"],
                demo_name=demo_name,
            )

        except Exception as e:
            logger.error(f"Error importing MAT file: {e}", exc_info=True)
            return None

    @staticmethod
    def import_dat(
        filepath: Path, name: str, node_color: str, demo_name: str
    ) -> Optional[Dataset]:
        """Import ASCII .dat or .txt file."""
        try:
            # Read metadata from first lines
            with open(filepath, "r") as f:
                header_lines = list(islice(f, 3))

            # Parse header
            channels = header_lines[1].strip().split("\t")
            units = header_lines[2].strip().split("\t")

            # Load data
            data = np.loadtxt(filepath, delimiter="\t", skiprows=3)

            # Ensure SL channel exists
            if "SL" not in channels:
                channels.append("SL")
                units.append("-")
                data = np.column_stack([data, np.zeros(len(data))])

            # Extract metadata
            metadata = DataImporter._extract_dat_metadata(header_lines[0], name, units)

            # Generate command channels
            channels, units, data = CmdChannelGenerator.create_cmd_channels(
                channels,
                units,
                data,
                metadata["unit_system"],
                metadata["sign_convention"],
            )

            # Map unit types
            unit_types = UnitSystemConverter.map_channels_to_types(channels)

            # Create dataset
            return Dataset(
                path=filepath,
                name=name,
                channels=channels,
                units=units,
                unit_types=unit_types,
                data=data,
                tire_id=metadata["tire_id"],
                rim_width=metadata["rim_width"],
                unit_system=metadata["unit_system"],
                sign_convention=metadata["sign_convention"],
                node_color=node_color,
                notes=metadata["notes"],
                demo_name=demo_name,
            )

        except Exception as e:
            logger.error(f"Error importing DAT file: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_mat_metadata(file_data: Dict, name: str) -> Dict[str, Any]:
        """Extract metadata from MAT file structure."""
        metadata = {
            "tire_id": "",
            "rim_width": 0,
            "unit_system": "USCS",
            "sign_convention": "SAE",
            "notes": "",
        }

        # Extract tire info
        if "tireid" in file_data:
            tire_info = file_data["tireid"][0].split(",")
            metadata["tire_id"] = tire_info[0]

            if len(tire_info) > 1:
                rim_match = re.search(r"\d+", tire_info[1])
                if rim_match:
                    metadata["rim_width"] = int(rim_match.group())

        # Extract unit system
        if "units" in file_data:
            metadata["unit_system"] = file_data["units"]
        else:
            # Infer from units if not specified
            if "channel" in file_data:
                units = (
                    np.concatenate(file_data["channel"][0][0][1][0]).ravel().tolist()
                )
                metadata["unit_system"] = "USCS" if "lb" in str(units) else "Metric"
            logger.warning(
                f"Unit system not specified in {name}, "
                f"inferred {metadata['unit_system']}"
            )

        # Extract sign convention
        if "sign" in file_data:
            metadata["sign_convention"] = file_data["sign"]
        else:
            logger.warning(
                f"Sign convention not specified in {name}, " f"defaulting to SAE"
            )

        # Extract notes
        if "notes" in file_data:
            metadata["notes"] = file_data["notes"]

        return metadata

    @staticmethod
    def _extract_dat_metadata(
        header_line: str, name: str, units: List[str]
    ) -> Dict[str, Any]:
        """Extract metadata from DAT file header."""
        metadata = {
            "tire_id": "",
            "rim_width": 0,
            "unit_system": "USCS",
            "sign_convention": "SAE",
            "notes": "",
        }

        # Extract tire name
        tire_match = re.search(r"Tire_Name=([^;]+)", header_line)
        if tire_match:
            metadata["tire_id"] = tire_match.group(1)

        # Extract rim width
        rim_match = re.search(r"Rim_Width=([^;]+)", header_line)
        if rim_match:
            metadata["rim_width"] = int(float(rim_match.group(1)))

        # Extract unit system
        unit_match = re.search(r"Unit_System=([^;]+)", header_line)
        if unit_match:
            metadata["unit_system"] = unit_match.group(1)
        else:
            metadata["unit_system"] = "USCS" if "lb" in units else "Metric"
            logger.warning(
                f"Unit system not specified in {name}, {metadata['unit_system']} "
                f"inferred from channel names."
            )

        # Extract sign convention
        sign_match = re.search(r"Sign_Convention=([^;]+)", header_line)
        if sign_match:
            metadata["sign_convention"] = sign_match.group(1)
        else:
            logger.warning(
                f"Sign convention not specified in {name}, defaulting to SAE"
            )

        # Extract notes
        notes_match = re.search(r"Notes=([^;]+)", header_line)
        if notes_match:
            metadata["notes"] = notes_match.group(1)

        return metadata


# Maintain backward compatibility with old function names
def import_mat(filepath, file_name, node_color, demo_name):
    """Legacy function for importing MAT files."""
    return DataImporter.import_mat(Path(filepath), file_name, node_color, demo_name)


def import_dat(filepath, file_name, node_color, demo_name):
    """Legacy function for importing DAT files."""
    return DataImporter.import_dat(Path(filepath), file_name, node_color, demo_name)


# Re-export for backward compatibility
dataset = Dataset
