import glob
import locale
import os
from locale import getlocale, setlocale
from contextlib import contextmanager
from enum import StrEnum
from typing import Tuple


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