# scripts/convention_conversion.py
from logger_setup import logger

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
    def convert_convention(cls, dataset, target_convention: str):
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
        # No conversion needed
        if dataset.sign_convention == target_convention:
            return dataset
        
        # Validate target convention
        if target_convention not in cls.SUPPORTED:
            raise ValueError(f"Unsupported target convention: {target_convention}")

        # Create a copy of the dataset to avoid modifying the original
        result = dataset.copy()

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