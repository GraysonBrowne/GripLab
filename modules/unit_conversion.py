# modules/unit_conversion.py
import math
from logger_setup import logger

class UnitSystemConverter:
    """
    Convert datasets between unit systems (USCS, Metric, SI).
    Also provides mapping from channel names to unit types.
    """

    # Known unit type definitions
    unit_types = {
        "length": ['RL', 'RE'],
        "force": ['FX', 'FY', 'FZ'],
        "torque": ['MX', 'MY', 'MZ'],
        "pressure": ['P'],
        "angle": ['SA', 'IA'],
        "speed": ['V'],
        "rotational_speed": ['N'],
        "temperature": ['RST', 'TSTI', 'TSTC', 'TSTO', 'AmbTmp'],
        "time": ['ET']
    }

    unit_definitions = {
        "length": {
            "SI"    : {"unit": "m", "factor": 1.0, "offset": 0},                  # base
            "Metric": {"unit": "cm", "factor": 0.01, "offset": 0},                # m → cm
            "USCS"  : {"unit": "in", "factor": 0.0254, "offset": 0},              # m → in
        },
        "force": {
            "SI"    : {"unit": "N", "factor": 1.0, "offset": 0},                  # base
            "Metric": {"unit": "N", "factor": 1.0, "offset": 0},                  # N → N
            "USCS"  : {"unit": "lb", "factor": 4.44822, "offset": 0},             # N → lb
        },
        "torque": {
            "SI"    : {"unit": "Nm", "factor": 1.0, "offset": 0},                 # base
            "Metric": {"unit": "Nm", "factor": 1.0, "offset": 0},                 # Nm → Nm
            "USCS"  : {"unit": "ft-lb", "factor": 1.35582, "offset": 0},          # Nm → ft-lb
        },
        "pressure": {
            "SI"    : {"unit": "Pa", "factor": 1.0, "offset": 0},                 # base
            "Metric": {"unit": "kPa", "factor": 0.001, "offset": 0},              # Pa → kPa
            "USCS"  : {"unit": "psi", "factor":6894.76, "offset": 0},             # Pa → psi
        },
        "angle": {
            "SI"    : {"unit": "rad", "factor": 1.0, "offset": 0},                # base
            "Metric": {"unit": "deg", "factor": math.pi/180, "offset": 0},        # rad → deg
            "USCS"  : {"unit": "deg", "factor": math.pi/180, "offset": 0},        # rad → deg
        },
        "speed": {
            "SI"    : {"unit": "m/s", "factor": 1.0, "offset": 0},                # base
            "Metric": {"unit": "kph", "factor": 1000/3600, "offset": 0},          # m/s → kph
            "USCS"  : {"unit": "mph", "factor": 0.44704, "offset": 0},            # m/s → mph
        },
        "rotational_speed": {
            "SI"    : {"unit": "rad/s", "factor": 1.0, "offset": 0},              # base
            "Metric": {"unit": "rpm", "factor": 2 * math.pi/60, "offset": 0},     # rad/s → rpm
            "USCS"  : {"unit": "rpm", "factor": 2 * math.pi/60, "offset": 0},     # rad/s → rpm
        },
        "temperature": {
            "SI"    : {"unit": "deg k", "factor": 1.0, "offset": 0},              # base
            "Metric": {"unit": "deg c", "factor": 1.0, "offset": 273.15},         # K → C
            "USCS"  : {"unit": "deg F", "factor": 5/9, "offset": (255.37,459.67)},# K → F
        },
        "time": {
            "SI"    : {"unit": "sec", "factor": 1.0, "offset": 0},                # base
            "Metric": {"unit": "sec", "factor": 1.0, "offset": 0},                # s → s
            "USCS"  : {"unit": "sec", "factor": 1.0, "offset": 0},                # s → s
        }
    } 

    @classmethod
    def map_channels_to_types(cls, channels: list) -> list:
        """
        Map each channel name to its unit type based on predefined dictionary.
        
        Args:
            channels: list of channel names

        Returns:
            list of unit types, aligned with input channels
        """
        try:
            # Build reverse lookup {channel -> unit_type}
            channel_to_type = {
                ch: t for t, chs in cls.unit_types.items() for ch in chs
            }

            # Map channels, use "none" if not found
            channel_types = [channel_to_type.get(ch, "none") for ch in channels]
            return channel_types
        except Exception as e:
            logger.error(f"Error determining unit types: {e}")
    
    @classmethod
    def convert_dataset(cls, dataset, to_system: str):
        """
        Convert dataset between unit systems if unit type is known.

        Args:
            dataset: The dataset to convert.
            to_system: "USCS" | "Metric" | "SI"

        Returns:
            dataset: The converted dataset with updated units and data.
        """
        try:
            # Validate target system
            from_system = dataset.unit_system
            if from_system == to_system:
                return dataset
            
            # Create a copy of the dataset to avoid modifying the original
            result = dataset.copy()

            # Prepare for conversion
            converted_data = result.data.copy()
            updated_units = []

            logger.info(f"Converting {result.name} from {from_system} to {to_system}")
            # Convert each channel based on its unit type
            for i, utype in enumerate(result.unit_types):
                if utype == "none":
                    updated_units.append("none")
                    continue

                # Get definitions
                defs = cls.unit_definitions[utype]
                from_def = defs[from_system]
                to_def = defs[to_system]

                # Handle temperature offset
                if isinstance(from_def["offset"], tuple):
                    from_offset = from_def["offset"][0]
                    to_offset = to_def["offset"]
                elif isinstance(to_def["offset"], tuple):
                    from_offset = from_def["offset"]
                    to_offset = to_def["offset"][1]
                else:
                    from_offset = from_def["offset"]
                    to_offset = to_def["offset"]

                if from_def["unit"] == to_def["unit"]:
                    # No conversion needed
                    converted_data[:, i] = converted_data[:, i] - from_offset
                    updated_units.append(to_def["unit"])
                    continue

                # Convert to SI (base)
                values_si = (converted_data[:, i] * from_def["factor"]) + from_offset

                # Convert SI → target
                converted_data[:, i] = (values_si / to_def["factor"]) - to_offset

                updated_units.append(to_def["unit"])

            # Update result with new unit system and converted data
            result.data = converted_data 
            result.unit_system = to_system
            result.units = updated_units

            logger.info(f"Conversion complete: {result.name} now in {to_system} system")
            return result
        except Exception as e:
            logger.error(f"Error converting units: {e}")