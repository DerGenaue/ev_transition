import html
import os

import requests
import re
import datetime
import babel.dates
import pandas as pd
from typing import List

from utils import PowerType, intor, newest_file_in_dir

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

    # Create an empty DataFrame with datetime index and specified columns
    df = pd.DataFrame(columns=columns, index=pd.DatetimeIndex([]))

    all_files = sorted(os.listdir(datafolder))
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

            month_year = babel.dates.format_date(ymonth, format='MMMM yyyy', locale='de_DE')
            print(month_year)
            assert data.iat[ystart + 5, 1] == month_year

            for j, kfztype in enumerate(kfztypes):
                l = ystart + 6 + j
                assert kfztype in data.iat[l, 1]
                total = intor(data.iat[l, 2])
                df.loc[ymonth, (kfztype, PowerType.BEV)] = intor(data.iat[l, 7])
                df.loc[ymonth, (kfztype, PowerType.FCEV)] = intor(data.iat[l, 8])
                df.loc[ymonth, (kfztype, PowerType.PHEV)] = intor(data.iat[l, 9])
                df.loc[ymonth, (kfztype, PowerType.HEV)] = intor(data.iat[l, 10])
                df.loc[ymonth, (kfztype, PowerType.Gas)] = intor(data.iat[l, -2])
                df.loc[ymonth, (kfztype, PowerType.HY)] = intor(data.iat[l, -1])
                assert df.loc[ymonth, kfztype].sum() == intor(data.iat[l, 3])
                df.loc[ymonth, (kfztype, PowerType.ICE)] = total - intor(data.iat[l, 3])
    
    df.sort_index(inplace=True)
    return df


def fz28_1_aggregated() -> pd.DataFrame:
    """
    Gets the aggregated table FZ 28.1 (from file cache if available):
    FZ 28.1 Neuzulassungen von Kraftfahrzeugen im September 2021 nach Fahrzeugklassen sowie nach ausgewählten Kraftstoffarten bzw. Energiequellen
    :return: A dataframe of monthly data aggregated by vehicle type (kfztypes) and power type
    """

    # Check if there is a data file newer than the cached pickle
    _, latest_mtime = newest_file_in_dir(datafolder, "fz28_*.xlsx")

    file = f"{datafolder}/fz28_1_aggregated.pkl"
    if os.path.exists(file) and os.path.getmtime(file) > latest_mtime:
        # if pickle exists and is newer than the latest file, load it
        return pd.read_pickle(file)

    # otherwise regenerate the pickle (and also CSV)
    df = fz28_1_do_aggregate()
    df.to_pickle(file)
    df.to_csv(f"{datafolder}/fz28_1_aggregated.csv")
    return df


def fz8_get_list() -> List[str]:
    """
    Get the Neuzulassungen von Kraftfahrzeugen und Kraftfahrzeugsanhängern statistics
    :param filter: Filter the files
    :return: All available Excel files
    """

    # https://www.kba.de/DE/Statistik/Produktkatalog/produkte/Fahrzeuge/fz8/fz8_gentab.html
    # https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ8/fz8_202508.xlsx?__blob=publicationFile&v=5
    # we just ignore the older PDF form data (< 2023):
    # https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ8/fz8_202212.pdf?__blob=publicationFile&v=2
    # Fetch webpage and regex search for links

    base_url = "https://www.kba.de"
    search_url = f"{base_url}/DE/Statistik/Produktkatalog/produkte/Fahrzeuge/fz8/fz8_gentab.html"

    try:
        response = requests.get(search_url)
        response.raise_for_status()

        # Find all Excel file links using regex
        excel_pattern = r'href="(/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ8/fz8_[^"]+\.xlsx[^"]+)'
        matches = re.finditer(excel_pattern, response.text)

        # Construct full URLs and filter if needed
        excel_links = [f"{base_url}{html.unescape(m.group(1))}" for m in matches]

        return excel_links

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


def fz8_3_segments_do_aggregate() -> pd.DataFrame:
    """
    Aggregates the downloaded monthly file data from table FZ 8.3 for segments:
    FZ 8.3 Neuzulassungen von Personenkraftwagen im Juli 2025 nach Segmenten, Modellreihen, Kraftstoffarten, CO2-Emissionen und Kraftstoffverbrauch
    :return: A dataframe of monthly PKW data aggregated by vehicle segment and power type
    """

    # Dataframe that will contain car type by fuel type by time
    columns = pd.MultiIndex.from_product([[], list(PowerType)], names=['Segment', 'Power Type'])

    # Create an empty DataFrame with datetime index and specified columns
    df = pd.DataFrame(columns=columns, index=pd.DatetimeIndex([]))

    all_files = sorted(os.listdir(datafolder))
    for i, file in enumerate(all_files):
        if m := re.match(r"fz8_([0-9]{4})([0-9]{2}).xlsx", file):
            year, month = m.groups()
            ymonth = datetime.date(int(year), int(month), 1)
            data = pd.read_excel(f"{datafolder}/{file}", sheet_name="FZ 8.3")

            # Some individual months apparently accidentally have a line missing, so we need to adjust
            ystart = 6 if data.iat[6, 1] == "Segment" else 5

            # sanity checks
            assert "Segment" == data.iat[ystart, 1]
            assert "Benzin" in data.iat[ystart + 1, 5]
            assert "Diesel" in data.iat[ystart + 1, 8]
            cngmissing = True
            if "CNG" in data.iat[ystart + 1, 11]:
                cngmissing = False
            assert "LPG" in data.iat[ystart + 1, -4]
            assert "Hybrid" in data.iat[ystart + 1, -3]
            assert "Plug-in" in data.iat[ystart + 2, -2]
            assert "BEV" in data.iat[ystart + 1, -1]

            month_year = babel.dates.format_date(ymonth, format='MMMM yyyy', locale='de_DE')
            print(month_year)
            assert month_year in data.iat[4, 1]

            for i in data.index:
                if m := re.match(r"((.+) ZUSAMMEN)|SONSTIGE", str(data.iat[i, 1])):
                    segment = m.group(2)
                    if not segment:
                        segment = "Sonstige"
                    total = intor(data.iat[i, 3])
                    df.loc[ymonth, (segment, PowerType.ICE_P)] = intor(data.iat[i, 5])
                    df.loc[ymonth, (segment, PowerType.ICE_D)] = intor(data.iat[i, 8])
                    if not cngmissing:
                        df.loc[ymonth, (segment, PowerType.CNG)] = intor(data.iat[i, 11])
                    df.loc[ymonth, (segment, PowerType.LPG)] = intor(data.iat[i, -4])
                    df.loc[ymonth, (segment, PowerType.HEV)] = intor(data.iat[i, -3])
                    df.loc[ymonth, (segment, PowerType.PHEV)] = intor(data.iat[i, -2])
                    df.loc[ymonth, (segment, PowerType.BEV)] = intor(data.iat[i, -1])
                    # TODO: diesel & benzin includes PHEV & HEV, so need to fix math
                    sum_specific = df.loc[ymonth, segment].sum()
                    df.loc[ymonth, (segment, PowerType.Other)] = total - sum_specific

    df.sort_index(inplace=True)
    return df


def fz8_3_segments_aggregated() -> pd.DataFrame:
    """
    Gets the aggregated table FZ 8.3 segments (from file cache if available):
    FZ 8.3 Neuzulassungen von Personenkraftwagen im Juli 2025 nach Segmenten, Modellreihen, Kraftstoffarten, CO2-Emissionen und Kraftstoffverbrauch
    :return: A dataframe of monthly PKW data aggregated by vehicle segment and power type
    """

    # Check if there is a data file newer than the cached pickle
    _, latest_mtime = newest_file_in_dir(datafolder, "fz8_*.xlsx")

    file = f"{datafolder}/fz8_3_segments_aggregated.pkl"
    if os.path.exists(file) and os.path.getmtime(file) > latest_mtime:
        # if pickle exists and is newer than the latest file, load it
        return pd.read_pickle(file)

    # otherwise regenerate the pickle (and also CSV)
    df = fz8_3_segments_do_aggregate()
    df.to_pickle(file)
    df.to_csv(f"{datafolder}/fz8_3_segments_aggregated.csv")
    return df


def fetch_all(files: List[str], only_new: bool = True) -> int:
    all_files = os.listdir(datafolder)

    fs = len(files)
    ndown = 0
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
            ndown += 1
        except requests.RequestException as e:
            print(f"Error fetching file data: {e}")
            continue

    return ndown


def ensure_up_to_date(force: bool = False):
    """
    Ensure all the latest files have been downloaded.
    By default only checks for new files once a day.
    :return:
    """
    _, time = newest_file_in_dir(datafolder, "fz28_*.xlsx")
    if force or datetime.datetime.fromtimestamp(time) < datetime.datetime.now() - datetime.timedelta(days=1):
        all_fz28 = fz28_get_list()
        # make sure at least the latest file is freshly downloaded
        if fetch_all(all_fz28) <= 0:
            fetch_all(all_fz28[:1], False)

    # ensure aggregate is up-to-date
    fz28_1_aggregated()

    
    _, time = newest_file_in_dir(datafolder, "fz8_*.xlsx")
    if force or datetime.datetime.fromtimestamp(time) < datetime.datetime.now() - datetime.timedelta(days=1):
        all_fz8 = fz8_get_list()
        # make sure at least the latest file is freshly downloaded
        if fetch_all(all_fz8) <= 0:
            fetch_all(all_fz8[:1], False)

    # ensure aggregate is up-to-date
    fz8_3_segments_aggregated()


if __name__ == "__main__":
    ensure_up_to_date()
    df = fz8_3_segments_aggregated()
    print(df)
