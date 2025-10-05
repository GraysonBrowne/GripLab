# core/processing.py
"""Signal processing utilities for tire test data."""

import numpy as np
from typing import Tuple, Optional, Union, List
from enum import Enum
from scipy.signal import butter, filtfilt

import panel as pn
from utils.logger import logger


class FilterType(Enum):
    """Types of filters available."""
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"
    BANDSTOP = "bandstop"


class DownsampleMethod(Enum):
    """Methods for downsampling data."""
    UNIFORM = "uniform"
    RANDOM = "random"
    GRID = "grid"


class SignalProcessor:
    """Handles signal processing operations for tire test data."""
    
    @staticmethod
    def apply_butterworth_filter(data: np.ndarray, cutoff: Union[float, Tuple[float, float]],
                                fs: float = 100, order: int = 4,
                                filter_type: FilterType = FilterType.LOWPASS) -> np.ndarray:
        """
        Apply a Butterworth filter to the data.
        
        Args:
            data: Input signal array
            cutoff: Cutoff frequency (Hz) or tuple of (low, high) for band filters
            fs: Sampling frequency (Hz)
            order: Filter order
            filter_type: Type of filter to apply
            
        Returns:
            Filtered signal array
        """
        try:
            nyquist = 0.5 * fs
            
            # Normalize cutoff frequency
            if isinstance(cutoff, tuple):
                normal_cutoff = [c / nyquist for c in cutoff]
            else:
                normal_cutoff = cutoff / nyquist
            
            # Design filter
            if filter_type == FilterType.LOWPASS:
                b, a = butter(order, normal_cutoff, btype='low', analog=False)
            elif filter_type == FilterType.HIGHPASS:
                b, a = butter(order, normal_cutoff, btype='high', analog=False)
            elif filter_type == FilterType.BANDPASS:
                b, a = butter(order, normal_cutoff, btype='band', analog=False)
            elif filter_type == FilterType.BANDSTOP:
                b, a = butter(order, normal_cutoff, btype='bandstop', analog=False)
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
            
            # Apply zero-phase filtering
            return filtfilt(b, a, data)
            
        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            return data
    
    @staticmethod
    def remove_outliers(data: np.ndarray, n_std: float = 3.0,
                       method: str = 'zscore') -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove outliers from data using statistical methods.
        
        Args:
            data: Input data array
            n_std: Number of standard deviations for outlier threshold
            method: Method to use ('zscore' or 'iqr')
            
        Returns:
            Tuple of (cleaned_data, outlier_mask)
        """
        try:
            if method == 'zscore':
                # Z-score method
                z_scores = np.abs((data - np.mean(data)) / np.std(data))
                outlier_mask = z_scores > n_std
            elif method == 'iqr':
                # Interquartile range method
                q1 = np.percentile(data, 25)
                q3 = np.percentile(data, 75)
                iqr = q3 - q1
                lower = q1 - n_std * iqr
                upper = q3 + n_std * iqr
                outlier_mask = (data < lower) | (data > upper)
            else:
                raise ValueError(f"Unknown outlier method: {method}")
            
            cleaned_data = data[~outlier_mask]
            return cleaned_data, outlier_mask
            
        except Exception as e:
            logger.error(f"Error removing outliers: {e}")
            return data, np.zeros(len(data), dtype=bool)


class DataDownsampler:
    """Handles downsampling of large datasets for visualization."""
    
    @staticmethod
    def downsample_uniform(x: np.ndarray, y: np.ndarray,
                          z: Optional[np.ndarray] = None,
                          c: Optional[np.ndarray] = None,
                          factor: int = 5) -> Tuple:
        """
        Downsample arrays uniformly by selecting every nth element.
        
        Args:
            x, y: Required data arrays
            z: Optional z-axis data
            c: Optional color data
            factor: Downsampling factor (select every nth point)
            
        Returns:
            Tuple of downsampled arrays
        """
        try:
            # Handle empty arrays
            if len(x) == 0 or len(y) == 0:
                logger.warning("Empty arrays provided for downsampling")
                if pn.state:
                    pn.state.notifications.warning(
                        'No data to plot under selected conditions',
                        duration=4000
                    )
                return x, y, z if z is not None else np.array([]), c if c is not None else np.array([])
            
            # Ensure arrays are numpy arrays
            x = np.asarray(x)
            y = np.asarray(y)
            z = np.asarray(z) if z is not None else np.array([])
            c = np.asarray(c) if c is not None else np.array([])
            
            # Downsample
            indices = slice(None, None, factor)
            
            return (
                x[indices],
                y[indices],
                z[indices] if len(z) > 0 else z,
                c[indices] if len(c) > 0 else c
            )
            
        except Exception as e:
            logger.error(f"Error downsampling data: {e}", exc_info=True)
            return x, y, z if z is not None else np.array([]), c if c is not None else np.array([])
    
    @staticmethod
    def downsample_random(x: np.ndarray, y: np.ndarray,
                         size: int = 2000, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Randomly downsample data to a target size.
        
        Args:
            x, y: Input data arrays
            size: Target number of points
            seed: Random seed for reproducibility
            
        Returns:
            Tuple of downsampled arrays
        """
        x = np.asarray(x)
        y = np.asarray(y)
        n = len(x)
        
        if n <= size:
            return x, y
        
        rng = np.random.default_rng(seed)
        indices = rng.choice(n, size, replace=False)
        
        return x[indices], y[indices]
    
    @staticmethod
    def downsample_grid(x: np.ndarray, y: np.ndarray,
                       size: int = 2000, bins: Tuple[int, int] = (50, 50),
                       seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Downsample using 2D grid binning for even coverage.
        
        Args:
            x, y: Input data arrays
            size: Target number of points
            bins: Number of bins (x_bins, y_bins)
            seed: Random seed for reproducibility
            
        Returns:
            Tuple of downsampled arrays
        """
        x = np.asarray(x)
        y = np.asarray(y)
        n = len(x)
        
        if n <= size:
            return x, y
        
        try:
            # Create 2D histogram bins
            x_edges = np.linspace(x.min(), x.max(), bins[0] + 1)
            y_edges = np.linspace(y.min(), y.max(), bins[1] + 1)
            
            # Find bin for each point
            x_idx = np.digitize(x, x_edges) - 1
            y_idx = np.digitize(y, y_edges) - 1
            
            # Clip to valid range
            x_idx = np.clip(x_idx, 0, bins[0] - 1)
            y_idx = np.clip(y_idx, 0, bins[1] - 1)
            
            # Map to linear bin index
            bin_index = x_idx * bins[1] + y_idx
            
            # Get unique bins and select one point per bin
            unique_bins, first_idx = np.unique(bin_index, return_index=True)
            
            # If still too many points, randomly select subset
            if len(unique_bins) > size:
                rng = np.random.default_rng(seed)
                chosen_bins = rng.choice(len(unique_bins), size, replace=False)
                indices = first_idx[chosen_bins]
            else:
                indices = first_idx
            
            return x[indices], y[indices]
            
        except Exception as e:
            logger.error(f"Error in grid downsampling: {e}")
            # Fallback to random sampling
            return DataDownsampler.downsample_random(x, y, size, seed)
    
    @staticmethod
    def smart_downsample(x: np.ndarray, y: np.ndarray,
                        z: Optional[np.ndarray] = None,
                        c: Optional[np.ndarray] = None,
                        target_points: int = 5000) -> Tuple:
        """
        Intelligently downsample based on data characteristics.
        
        Args:
            x, y: Required data arrays
            z: Optional z-axis data
            c: Optional color data
            target_points: Target number of points
            
        Returns:
            Tuple of downsampled arrays
        """
        n_points = len(x)
        
        # No downsampling needed
        if n_points <= target_points:
            return x, y, z, c
        
        # Calculate appropriate factor
        factor = max(1, n_points // target_points)
        
        # Use uniform downsampling for consistent spacing
        return DataDownsampler.downsample_uniform(x, y, z, c, factor)


# Legacy function names for backward compatibility
def low_pass_filter(data: np.ndarray, cutoff_hz: float, fs: float = 100,
                   order: int = 4) -> np.ndarray:
    """Legacy function for low-pass filtering."""
    return SignalProcessor.apply_butterworth_filter(
        data, cutoff_hz, fs, order, FilterType.LOWPASS
    )


def downsample_uniform(x, y, z=None, c=None, factor=5):
    """Legacy function for uniform downsampling."""
    # Handle the legacy interface where z and c might be empty lists
    z = np.array(z) if z is not None and len(z) > 0 else None
    c = np.array(c) if c is not None and len(c) > 0 else None
    return DataDownsampler.downsample_uniform(x, y, z, c, factor)


def downsample_xy(x, y, size=2000, method="random", bins=(50, 50), seed=None):
    """Legacy function for 2D downsampling."""
    if method == "random":
        return DataDownsampler.downsample_random(x, y, size, seed)
    elif method == "grid":
        return DataDownsampler.downsample_grid(x, y, size, bins, seed)
    else:
        raise ValueError(f"Unknown method: {method}")