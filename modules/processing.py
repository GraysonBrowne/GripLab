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