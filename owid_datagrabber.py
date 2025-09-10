import html
import os

import requests
import re
import datetime
import babel.dates
import pandas as pd
from typing import List

from utils import PowerType, intor, newest_file_in_dir

datafolder = "data/owid"




def owid_electric_car_sales() -> pd.DataFrame:
    # https://docs.google.com/spreadsheets/d/e/2PACX-1vRDQ1EYuQPZasmbfjaghH9f65Nd2yLkQ0QAnOP5bp0LHWkwnjVcwssk6VFDhmWPOzjw2gCFyOqXBTQU/pub?output=csv
    # https://docs.google.com/spreadsheets/d/e/2PACX-1vRDQ1EYuQPZasmbfjaghH9f65Nd2yLkQ0QAnOP5bp0LHWkwnjVcwssk6VFDhmWPOzjw2gCFyOqXBTQU/pub?gid=409110122&output=csv
    data = pd.read_csv(os.path.join(datafolder, 'Electric car sales (IEA, 2025) - data.csv'), index_col=['Entity', 'year'])
    return data


def ensure_up_to_date(force: bool = False):
    """
    Ensure all the latest files have been downloaded.
    By default only checks for new files once a day.
    :return:
    """
    # pass


if __name__ == "__main__":
    ensure_up_to_date()
