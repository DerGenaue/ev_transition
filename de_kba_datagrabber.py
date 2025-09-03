import html
import os

import requests
import re
import datetime
import locale
import pandas as pd
from typing import List

from utils import override_locale, PowerType, intor

datafolder = "data/de-kba"

kfztypes = ["Krafträder", "Personenkraftwagen", "Kraftomnibusse", "Lastkraftwagen", "Zugmaschinen insgesamt",
            "Sattelzugmaschinen", "Sonstige Kfz"]


def fz28_get_list() -> List[str]:
    """
    Get the Neuzulassungen Alternative Antriebe statistics
    :param filter: Filter the files
    :return: All available Excel files
    """

    # https://www.kba.de/DE/Statistik/Produktkatalog/produkte/Fahrzeuge/fz28/fz28_gentab.html
    # https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ28/fz28_2025_07.xlsx?__blob=publicationFile&v=2
    # Fetch webpage and regex search for links

    base_url = "https://www.kba.de"
    search_url = f"{base_url}/DE/Statistik/Produktkatalog/produkte/Fahrzeuge/fz28/fz28_gentab.html"

    try:
        response = requests.get(search_url)
        response.raise_for_status()

        # Find all Excel file links using regex
        excel_pattern = r'href="(/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ28/fz28_[^"]+\.xlsx[^"]+)'
        matches = re.finditer(excel_pattern, response.text)

        # Construct full URLs and filter if needed
        excel_links = [f"{base_url}{html.unescape(m.group(1))}" for m in matches]

        return excel_links

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


def fz28_1_do_aggregate() -> pd.DataFrame:
    """
    Aggregates the downloaded monthly file data from table FZ 28.1:
    FZ 28.1 Neuzulassungen von Kraftfahrzeugen im September 2021 nach Fahrzeugklassen sowie nach ausgewählten Kraftstoffarten bzw. Energiequellen
    :return: A dataframe of monthly data aggregated by vehicle type (kfztypes) and power type
    """

    # Dataframe that will contain car type by fuel type by time
    columns = pd.MultiIndex.from_product([kfztypes, list(PowerType)], names=['Vehicle Type', 'Power Type'])

    # Create an empty DataFrame with empty index and specified columns
    df = pd.DataFrame(columns=columns)

    all_files = os.listdir(datafolder)
    for i, file in enumerate(all_files):
        if m := re.match(r"fz28_([0-9]+)_([0-9]+).xlsx", file):
            year, month = m.groups()
            ymonth = datetime.date(int(year), int(month), 1)
            data = pd.read_excel(f"{datafolder}/{file}", sheet_name="FZ 28.1")

            # Some individual months apparently accidentally have a line missing, so we need to adjust
            ystart = 6 if data.iat[6, 1] == "Fahrzeugklasse" else 5

            # sanity checks
            assert "Fahrzeugklasse" == data.iat[ystart, 1]
            assert "Elektro" in data.iat[ystart + 4, 7]
            assert "Brennstoffzelle" in data.iat[ystart + 4, 8]
            assert "Plug-in-Hybrid" in data.iat[ystart + 4, 9]
            assert "Hybrid" in data.iat[ystart + 2, 10]
            assert "insgesamt" in data.iat[ystart + 3, 10]
            assert "Gas" in data.iat[ystart + 2, -2]
            assert "Wasserstoff" in data.iat[ystart + 2, -1]
            with override_locale(locale.LC_TIME, 'de_DE'):
                print(f"{ymonth:%B %Y}")
                assert data.iat[ystart + 5, 1] == f"{ymonth:%B %Y}"

            for j, kfztype in enumerate(kfztypes):
                l = ystart + 6 + j
                assert kfztype in data.iat[l, 1]
                total = intor(data.iat[l, 2])
                df.loc[ymonth, (kfztype, PowerType.BEV)] = intor(data.iat[l, 7])
                df.loc[ymonth, (kfztype, PowerType.FCEV)] = intor(data.iat[l, 8])
                df.loc[ymonth, (kfztype, PowerType.PHEV)] = intor(data.iat[l, 9])
                df.loc[ymonth, (kfztype, PowerType.HEV)] = intor(data.iat[l, 10])
                df.loc[ymonth, (kfztype, PowerType.CNG)] = intor(data.iat[l, -2])
                df.loc[ymonth, (kfztype, PowerType.HCE)] = intor(data.iat[l, -1])
                assert df.loc[ymonth, kfztype].sum() == intor(data.iat[l, 3])
                df.loc[ymonth, (kfztype, PowerType.ICE)] = total - intor(data.iat[l, 3])

    return df


def fz28_1_aggregated() -> pd.DataFrame:
    """
    Gets the aggregated table FZ 28.1 (from file cache if available):
    FZ 28.1 Neuzulassungen von Kraftfahrzeugen im September 2021 nach Fahrzeugklassen sowie nach ausgewählten Kraftstoffarten bzw. Energiequellen
    :return: A dataframe of monthly data aggregated by vehicle type (kfztypes) and power type
    """

    # find newest file
    all_files = os.listdir(datafolder)
    latest_mtime = max(
        (os.path.getmtime(os.path.join(datafolder, filename))
         for filename in all_files
         if re.match(r"fz28_([0-9_]+).xlsx", filename)),
        default=None
    )

    file = f"{datafolder}/fz28_1_aggregated.pkl"
    if os.path.exists(file) and os.path.getmtime(file) > latest_mtime:
        # if pickle exists and is newer than the latest file, load it
        return pd.read_pickle(file)

    # otherwise regenerate the pickle (and also CSV)
    df = fz28_1_do_aggregate()
    df.to_pickle(file)
    df.to_csv(f"{datafolder}/fz28_1_aggregated.csv")
    return df


def fetch_all(files: List[str], only_new: bool = True):
    all_files = os.listdir(datafolder)

    fs = len(files)
    for i, file in enumerate(files):
        # get only the filename of the file
        fname = file.split("/")[-1].split("?")[0]
        print(f"File ({i}/{fs}): {fname} .. ", end="")
        if fname in all_files and only_new:
            print(f"already exists.")
            continue

        print(f"downloading .. ", end="")
        try:
            response = requests.get(file)
            response.raise_for_status()
            with open(f"{datafolder}/{fname}", "wb") as f:
                f.write(response.content)
            print(f"Success")
        except requests.RequestException as e:
            print(f"Error fetching file data: {e}")
            continue


if __name__ == "__main__":
    all_fz28 = fz28_get_list()
    fetch_all(all_fz28)
    df = fz28_1_aggregated()
    print(df)
