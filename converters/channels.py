# converters/channels.py
"""Container for channel labels and other metadata."""

from typing import Dict

class ChannelMetadata:

    CHANNEL_LABELS: Dict[str, str] = {
        # Forces
        "FX": "Longitudinal Force",
        "FY": "Lateral Force",
        "FZ": "Normal Force",
        "CmdFZ": "Commanded Normal Force",
        # Moments
        "MX": "Overturning Moment",
        "MY": "Rolling Resistance Moment",
        "MZ": "Aligning Moment",
        # Angles
        "IA": "Inclination Angle",
        "SA": "Slip Angle",
        "CmdIA": "Commanded Inclination Angle",
        "CmdSA": "Commanded Slip Angle",
        # Ratios
        "SR": "Slip Ratio (Machine Control)",
        "SL": "Slip Ratio",
        "NFX": "Normalized Longitudinal Force",
        "NFY": "Normalized Lateral Force",
        # Lengths
        "RL": "Loaded Radius",
        "RE": "Effective Rolling Radius",
        # Pressure
        "P": "Pressure",
        "CmdP": "Commanded Pressure",
        # Speed
        "V": "Road Speed",
        "N": "Wheel Rotation Speed",
        "CmdV": "Commanded Road Speed",
        # Temperature
        "RST": "Road Surface Temperature",
        "TSTI": "Tire Surface Temperature - Inside",
        "TSTC": "Tire Surface Temperature - Center",
        "TSTO": "Tire Surface Temperature - Outside",
        "AMBTMP": "Ambient Temperature",
        # Time
        "ET": "Elapsed Time",
    }

    @classmethod
    def get_label(cls, channel: str) -> str:
        """Return the standard display label for a channel, or the channel name if unknown."""
        return cls.CHANNEL_LABELS.get(channel, channel)
