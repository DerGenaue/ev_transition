import os

import requests
import re
from typing import List


datafolder = "data/de-kba"

def get_fz28() -> List[str]:
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
        excel_pattern = r'href="(/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ28/fz28_[^"]+\.xlsx)'
        matches = re.finditer(excel_pattern, response.text)

        # Construct full URLs and filter if needed
        excel_links = [f"{base_url}{m.group(1)}" for m in matches]

        return excel_links

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


def fetch_all(files: List[str], only_new: bool = True):
    # List all files in folder
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
    all_fz28 = get_fz28()
    fetch_all(all_fz28)