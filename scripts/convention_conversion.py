# scripts/convention_conversion.py

class ConventionConverter:
    # Scale factors for various channels in different conventions
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
