# modules/processing.py
import numpy as np
from scipy.signal import butter, filtfilt

def low_pass_filter(data, cutoff_hz, fs=100, order=4):
    """
    Apply a low-pass Butterworth filter.
    
    Parameters:
        data (array-like): Input signal.
        cutoff_hz (float): Cutoff frequency in Hz.
        fs (float): Sampling frequency (Hz). Default 100 Hz for 10 ms sampling.
        order (int): Filter order. Default 4.
        
    Returns:
        np.ndarray: Filtered signal.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_hz / nyquist
    
    # Design Butterworth filter
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    
    # Apply with zero-phase filtering
    y = filtfilt(b, a, data)
    
    return y

def downsample_uniform(x, y, z=[], c=[],factor=5):
    """
    Downsamples the input arrays uniformly by selecting every nth element.

    Parameters:
        x (array-like): The input array of x-values.
        y (array-like): The input array of y-values.
        factor (int, optional): The downsampling factor. Every 'factor'-th 
            element is selected. Default is 5.

    Returns:
        tuple: Two arrays containing the downsampled x and y values.
    """
    if (len(z) != 0) and len(c != 0):
        return x[::factor], y[::factor], z[::factor], c[::factor]
    elif (len(z) != 0):
        return x[::factor], y[::factor], z[::factor]
    elif len(c != 0):
        return x[::factor], y[::factor], c[::factor]
    else:   
        return x[::factor], y[::factor]

def downsample_xy(x, y, size=2000, method="random", bins=(50, 50), seed=None):
    """
    Downsample two independent channels for scatter plotting.
    
    Parameters
    ----------
    x, y : array-like
        Input data arrays of the same length.
    size : int, optional
        Approximate number of points to return (default 2000).
    method : {'random', 'grid'}, optional
        - 'random': uniform random sampling
        - 'grid'  : binning in 2D space, ensures even coverage
    bins : tuple of int, optional
        Number of bins (x_bins, y_bins) for grid method (default 50x50).
    seed : int, optional
        Random seed for reproducibility.
    
    Returns
    -------
    x_ds, y_ds : np.ndarray
        Downsampled arrays.
    """
    x = np.asarray(x)
    y = np.asarray(y)
    n = len(x)

    if n <= size:
        return x, y  # already small enough
    
    rng = np.random.default_rng(seed)

    if method == "random":
        idx = rng.choice(n, size, replace=False)
        return x[idx], y[idx]

    elif method == "grid":
        # Create 2D histogram bins
        x_bins = np.linspace(x.min(), x.max(), bins[0] + 1)
        y_bins = np.linspace(y.min(), y.max(), bins[1] + 1)

        # Digitize to find bin for each point
        x_idx = np.digitize(x, x_bins) - 1
        y_idx = np.digitize(y, y_bins) - 1

        # Map each point to a 2D bin index
        bin_index = x_idx * bins[1] + y_idx

        # For each bin, randomly keep 1 sample (or more if size allows)
        unique_bins, first_idx = np.unique(bin_index, return_index=True)

        # If too many bins, reduce randomly
        if len(unique_bins) > size:
            chosen_bins = rng.choice(len(unique_bins), size, replace=False)
            idx = first_idx[chosen_bins]
        else:
            idx = first_idx

        return x[idx], y[idx]

    else:
        raise ValueError("method must be 'random' or 'grid'")