# scripts/unit_conversion.py
"""Optimized unit system conversion utilities for GripLab application."""

import math
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import replace

from .logger_setup import logger


class UnitSystemConverter:
    """High-performance unit system converter."""
    
    # Pre-computed conversion factors for direct access
    # Structure: [from_system][to_system][unit_type] = (factor, offset)
    _CONVERSION_CACHE: Dict[str, Dict[str, Dict[str, Tuple[float, Any]]]] = {}
    
    # Static channel mappings (no Enum overhead)
    CHANNEL_TO_TYPE = {
        # Length channels
        'RL': 'length', 'RE': 'length',
        # Force channels
        'FX': 'force', 'FY': 'force', 'FZ': 'force', 'CmdFZ': 'force',
        # Torque channels
        'MX': 'torque', 'MY': 'torque', 'MZ': 'torque',
        # Pressure channels
        'P': 'pressure', 'CmdP': 'pressure',
        # Angle channels
        'SA': 'angle', 'IA': 'angle', 'CmdSA': 'angle', 'CmdIA': 'angle',
        # Speed channels
        'V': 'speed', 'CmdV': 'speed',
        # Rotational speed
        'N': 'rotational_speed',
        # Temperature channels
        'RST': 'temperature', 'TSTI': 'temperature',
        'TSTC': 'temperature', 'TSTO': 'temperature', 'AmbTmp': 'temperature',
        # Time
        'ET': 'time'
    }
    
    # Direct unit definitions (avoiding object creation)
    # Structure: [unit_type][system] = (unit_string, to_si_factor, offset)
    UNIT_DEFS = {
        'length': {
            'SI': ('m', 1.0, 0),
            'Metric': ('cm', 0.01, 0),
            'USCS': ('in', 0.0254, 0),
        },
        'force': {
            'SI': ('N', 1.0, 0),
            'Metric': ('N', 1.0, 0),
            'USCS': ('lb', 4.44822, 0),
        },
        'torque': {
            'SI': ('Nm', 1.0, 0),
            'Metric': ('Nm', 1.0, 0),
            'USCS': ('ft-lb', 1.35582, 0),
        },
        'pressure': {
            'SI': ('Pa', 1.0, 0),
            'Metric': ('kPa', 1000, 0),
            'USCS': ('psi', 6894.76, 0),
        },
        'angle': {
            'SI': ('rad', 1.0, 0),
            'Metric': ('deg', math.pi/180, 0),
            'USCS': ('deg', math.pi/180, 0),
        },
        'speed': {
            'SI': ('m/s', 1.0, 0),
            'Metric': ('kph', 1000/3600, 0),
            'USCS': ('mph', 0.44704, 0),
        },
        'rotational_speed': {
            'SI': ('rad/s', 1.0, 0),
            'Metric': ('rpm', 2 * math.pi/60, 0),
            'USCS': ('rpm', 2 * math.pi/60, 0),
        },
        'temperature': {
            'SI': ('deg k', 1.0, 0),
            'Metric': ('deg c', 1.0, 273.15),
            'USCS': ('deg F', 5/9, (255.37, 459.67)),
        },
        'time': {
            'SI': ('sec', 1.0, 0),
            'Metric': ('sec', 1.0, 0),
            'USCS': ('sec', 1.0, 0),
        }
    }
    
    @classmethod
    def _initialize_cache(cls):
        """Pre-compute all conversion factors for fast lookup."""
        if cls._CONVERSION_CACHE:
            return  # Already initialized
        
        systems = ['SI', 'Metric', 'USCS']
        
        for from_sys in systems:
            cls._CONVERSION_CACHE[from_sys] = {}
            for to_sys in systems:
                cls._CONVERSION_CACHE[from_sys][to_sys] = {}
                
                for unit_type, defs in cls.UNIT_DEFS.items():
                    if from_sys == to_sys:
                        # No conversion needed
                        cls._CONVERSION_CACHE[from_sys][to_sys][unit_type] = (1.0, 0, 0)
                    else:
                        from_def = defs[from_sys]
                        to_def = defs[to_sys]
                        
                        to_si = from_def[1]
                        from_si = to_def[1]
                        
                        # Handle offsets
                        if isinstance(from_def[2], tuple):
                            from_offset = from_def[2][0]
                            to_offset = to_def[2]
                        elif isinstance(to_def[2], tuple):
                            from_offset = from_def[2]
                            to_offset = to_def[2][1]
                        else:
                            from_offset = from_def[2]
                            to_offset = to_def[2]
                        
                        cls._CONVERSION_CACHE[from_sys][to_sys][unit_type] = (
                            to_si, from_si, from_offset, to_offset
                        )
    
    @classmethod
    def map_channels_to_types(cls, channels: List[str]) -> List[str]:
        """
        Fast mapping of channels to unit types.
        
        Args:
            channels: List of channel names
            
        Returns:
            List of unit type strings
        """
        # Use list comprehension with dict.get for speed
        return [cls.CHANNEL_TO_TYPE.get(ch, '-') for ch in channels]
    
    @classmethod
    def convert_dataset(cls, dataset: Any, to_system: str) -> Any:
        """
        Optimized dataset conversion.
        
        Args:
            dataset: Dataset object with unit_system, unit_types, data, etc.
            to_system: Target unit system name
            
        Returns:
            New dataset with converted values
        """
        from_system = dataset.unit_system
        
        # Quick return if no conversion needed
        if from_system == to_system:
            return dataset
        
        # Initialize cache on first use
        if not cls._CONVERSION_CACHE:
            cls._initialize_cache()
        
        # Validate systems
        if from_system not in cls._CONVERSION_CACHE or to_system not in cls._CONVERSION_CACHE:
            logger.error(f"Invalid unit systems: {from_system} -> {to_system}")
            return dataset
        
        try:
            # Get conversion factors for this system pair
            conversions = cls._CONVERSION_CACHE[from_system][to_system]
            
            # Create dataset copy
            result = replace(dataset, data=dataset.data.copy())
            updated_units = []

            # Identify command channel indexes for rounding
            channels = result.channels
            cmd_channels = [s for s in channels if 'Cmd' in s]
            cmd_indexes = [channels.index(s) for s in cmd_channels]
            
            # Vectorized conversion where possible
            for i, unit_type_str in enumerate(result.unit_types):
                if unit_type_str == '-':
                    updated_units.append('-')
                    continue
                
                # Get conversion parameters
                if unit_type_str not in conversions:
                    updated_units.append(result.units[i])
                    continue
                
                to_si, from_si, from_offset, to_offset = conversions[unit_type_str]
                
                # Get the target unit string
                to_unit = cls.UNIT_DEFS[unit_type_str][to_system][0]
                updated_units.append(to_unit)
                
                # Skip if no conversion needed (factor == 1 and no offsets)
                if (to_si / from_si) == 1.0 and from_offset == 0 and to_offset == 0:
                    continue
                
                # Vectorized conversion for entire column
                if from_offset != 0 or to_offset != 0:
                    # With offsets (e.g., temperature)
                    result.data[:, i] = (result.data[:, i] * to_si + from_offset) / from_si - to_offset
                else:
                    # Simple multiplication (most common case)
                    result.data[:, i] *= (to_si / from_si)
                
                if i in cmd_indexes:
                    result.data[:, i] = np.round(result.data[:, i])

            result.units = updated_units
            result.unit_system = to_system
            
            logger.info(f"Converted dataset from {from_system} to {to_system}")
            return result
            
        except Exception as e:
            logger.error(f"Error converting dataset: {e}", exc_info=True)
            return dataset
    
    @classmethod
    def convert_dataset_fast(cls, dataset: Any, to_system: str) -> Any:
        """
        Ultra-fast conversion using NumPy broadcasting.
        Assumes data is already validated.
        
        Args:
            dataset: Dataset object
            to_system: Target unit system
            
        Returns:
            Converted dataset
        """
        from_system = dataset.unit_system
        
        if from_system == to_system:
            return dataset
        
        # Initialize cache
        if not cls._CONVERSION_CACHE:
            cls._initialize_cache()
        
        # Create result
        result = replace(dataset)
        result.data = dataset.data.copy()
        
        # Get all conversion factors at once
        conversions = cls._CONVERSION_CACHE[from_system][to_system]
        
        # Build conversion arrays
        n_channels = len(result.unit_types)
        to_sis = np.ones(n_channels)
        from_sis = np.ones(n_channels)
        from_offsets = np.zeros(n_channels)
        to_offsets = np.zeros(n_channels)
        updated_units = []
        
        for i, unit_type in enumerate(result.unit_types):
            if unit_type == '-':
                updated_units.append('-')
            elif unit_type in conversions:
                to_si, from_si, from_off, to_off = conversions[unit_type]
                to_sis[i] = to_si
                from_sis[i] = from_si
                from_offsets[i] = from_off
                to_offsets[i] = to_off
                updated_units.append(cls.UNIT_DEFS[unit_type][to_system][0])
            else:
                updated_units.append(result.units[i])
        
        # Apply conversion using broadcasting
        # This is much faster than loop for large datasets
        if np.any(from_offsets != 0) or np.any(to_offsets != 0):
            result.data = (result.data*to_sis + from_offsets) / from_sis - to_offsets
        else:
            result.data *= (to_sis / from_sis)
        
        result.units = updated_units
        result.unit_system = to_system
        
        return result
    
    @classmethod
    def convert_value(cls, value: float, unit_type: str,
                     from_system: str, to_system: str) -> float:
        """
        Fast single value conversion.
        
        Args:
            value: Value to convert
            unit_type: Type of unit
            from_system: Source system
            to_system: Target system
            
        Returns:
            Converted value
        """
        if from_system == to_system:
            return value
        
        # Initialize cache if needed
        if not cls._CONVERSION_CACHE:
            cls._initialize_cache()
        
        try:
            to_si, from_si, from_offset, to_offset = cls._CONVERSION_CACHE[from_system][to_system][unit_type]
            return (value*to_si + from_offset) / from_si - to_offset
        except KeyError:
            return value