import glob
import locale
import os
from locale import getlocale, setlocale
from contextlib import contextmanager
from enum import StrEnum
from typing import Tuple

import numpy as np
import pandas as pd


class PowerType(StrEnum):
    """Enum representing different vehicle power types"""

    ICE = "ICE"
    """Internal Combustion Engine - Traditional fossil fuel powered vehicles (Diesel / Petrol)"""
    
    ICE_D = "ICE_D"
    """Internal Combustion Engine - Using Diesel as fuel"""

    ICE_P = "ICE_P"
    """Internal Combustion Engine - Using Petrol as fuel"""

    BEV = "BEV"
    """Battery Electric Vehicle - Fully electric vehicles powered by rechargeable batteries"""

    FCEV = "FCEV"
    """Fuel Cell Electric Vehicle - Vehicles powered by hydrogen fuel cells"""

    PHEV = "PHEV"
    """Plug-in Hybrid Electric Vehicle - Hybrid vehicles with rechargeable batteries"""

    HEV = "HEV"
    """Hybrid Electric Vehicle - Vehicles combining combustion engine with electric motor, but without charging"""
    HEV_D = "HEV_D"
    """Hybrid Electric Vehicle - HEVs using diesel fuel"""
    HEV_P = "HEV_P"
    """Hybrid Electric Vehicle - HEVs using petrol fuel"""

    Gas = "Gas"
    """CNG or LPG - Vehicles powered by gaseous fuel"""
    CNG = "CNG"
    """Compressed Natural Gas - Vehicles powered by natural gas"""
    LPG = "LPG"
    """LPG - Liquefied Petroleum Gas"""

    HCE = "HCE"
    """Hydrogen Combustion Engine - Vehicles with hydrogen-powered combustion engines"""
    
    HY = "HY"
    """Hydrogen - Unclear specification if HCE or FCEV"""


def intor(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def floator(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def newest_file_in_dir(dir_name, file_glob='*') -> Tuple[str, float]:
    fmax = max(glob.glob(os.path.join(dir_name, file_glob)), key=os.path.getmtime, default=None)
    if fmax is None:
        return '', 0
    return os.path.basename(fmax), os.path.getmtime(fmax)



def correlate_slice_normalized(a: np.ndarray, v: np.ndarray, epsilon=0.001) -> Tuple[np.ndarray, np.ndarray]:
    """
    Correlate a and v normalized to the maximum possible correlation for each offset (boundary effects!)
    """
    if len(v) > len(a):
        a, v = v, a
    # fix nans
    a, v = np.nan_to_num(a), np.nan_to_num(v)
    L, l = len(a), len(v)
    offsets = np.arange(-l+2,L+1)
    norm_by_slice_a = np.correlate(a*a, np.ones(v.shape), mode='full')
    norm_by_slice_v = np.correlate(np.ones(a.shape), v*v, mode='full')
    corrs = 2 * np.correlate(a, v, mode='full') / (norm_by_slice_a + norm_by_slice_v + epsilon)
    return offsets, corrs

def df_shift_index(df: pd.DataFrame, n) -> pd.DataFrame:
    """ Shifts the index of a dataframe by n """
    df = df.copy()
    df.index = df.index + n
    return df

def frequency_in_year(freq):
    return len(pd.date_range(start=pd.Timestamp('2000-01-01'), end=pd.Timestamp('2000-12-31'), freq=freq, normalize=True))

def delta_frequency_to_string(dt, freq):
    fy = frequency_in_year(freq)
    sign = '' if dt >= 0 else '-'
    dt = abs(dt)
    y = int(dt / fy)
    r = dt % fy
    
    result = []
    
    if y != 0:
        result.append(f"{y} year{'' if abs(y) == 1 else 's'}")
    
    
    if r != 0:
        if fy == 4:
            funit = 'quarter'
        elif fy == 12:
            funit = 'month'
        elif fy == 52:
            funit = 'week'
        elif fy < 367:
            funit = 'day'
        else:
            funit = ''
        result.append(f"{r} {funit}{'' if abs(r)==1 else 's'}")
    
    return sign + ' '.join(result)