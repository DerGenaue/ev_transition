from locale import getlocale, setlocale
from contextlib import contextmanager
from enum import StrEnum


class PowerType(StrEnum):
    """Enum representing different vehicle power types"""

    ICE = "ICE"
    """Internal Combustion Engine - Traditional fossil fuel powered vehicles"""

    BEV = "BEV"
    """Battery Electric Vehicle - Fully electric vehicles powered by rechargeable batteries"""

    FCEV = "FCEV"
    """Fuel Cell Electric Vehicle - Vehicles powered by hydrogen fuel cells"""

    PHEV = "PHEV"
    """Plug-in Hybrid Electric Vehicle - Hybrid vehicles with rechargeable batteries"""

    HEV = "HEV"
    """Hybrid Electric Vehicle - Vehicles combining combustion engine with electric motor"""

    CNG = "CNG"
    """Compressed Natural Gas - Vehicles powered by natural gas"""

    HCE = "HCE"
    """Hydrogen Combustion Engine - Vehicles with hydrogen-powered combustion engines"""


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

@contextmanager
def override_locale(category, locale_string):
    prev_locale_string = getlocale(category)
    setlocale(category, locale_string)
    yield
    setlocale(category, prev_locale_string)