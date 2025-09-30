import json
import re

import pandas as pd
from unidecode import unidecode

def aggregate_adac_price_data(ignore_manufacture_end_before=2020) -> pd.DataFrame:

    # Files have ben manually created using the ADAC Autosuche
    with open('../ADAC-AllData-names.json', 'r', encoding='utf-8') as file:
        name_map = json.load(file)
    with open('../ADAC-AllData.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Process and aggregate the data
    aggregated_data = pd.DataFrame(columns=['NAME', 'fuelType', 'min_price', 'max_price', 'avg_price', 'med_price'])
    aggregated_data.set_index(['NAME', 'fuelType'], inplace=True)

    for name in set(data.keys()).union(set(name_map.keys())):
        
        mapped_names = name
        # re-aggregate data according to name_map
        if name in name_map:
            mapped_names = name_map[name]
        # if name is an array
        if type(mapped_names) is not list:
            mapped_names = [mapped_names]
        
        
        tmp = []
        for n in mapped_names:
            if n in data and data[n]['items']:
        
                for item in data[n]['items']:
                    if item['manufacturedUntil'] is not None and item['manufacturedUntil'] < ignore_manufacture_end_before:
                        continue
                    for c in item['cars']:
                        
                        full_name_concat = filter(None, [item['brandTerm'], item['modelTerm'], item['alternativeModelTerm'], c['name']])
                        full_name_concat = ' '.join(full_name_concat)
                        
                        if not match_car_name(full_name_concat, n):
                            print('Ignoring mismatched car: ', n, ' | ', full_name_concat)
                            continue
                        
                        if c['basePrice'] > 0: # ignore basePrice of 0
                            tmp.append({c['fuelType']: c['basePrice']})
        
        if not tmp:
            print('No recent cars with price info for: ', name)
        
        tmp_df = pd.DataFrame(tmp)
        
        # for each fuelType column calculate min, max and avg price and add to aggregated_data
        for fuel_type in tmp_df.columns:
            if not tmp_df[fuel_type].empty:
                aggregated_data.loc[(name, fuel_type), :] = [
                    tmp_df[fuel_type].min(),
                    tmp_df[fuel_type].max(),
                    tmp_df[fuel_type].mean(),
                    tmp_df[fuel_type].median(),
                ]
    aggregated_data.sort_index(inplace=True)
    return aggregated_data


def match_car_name(haystack, needle) -> bool:
    """ Returns whether the needle appears to match the haystack car name """
    haystack = unidecode(haystack).lower()
    needle = unidecode(needle).lower()
    for npart in needle.split(' '):
        if re.search(f'(?<!\\w){re.escape(npart)}(?!\\w)', haystack) is None:
            return False
    return True


def save_aggregated_price_data():
    result = aggregate_adac_price_data()
    result.to_pickle('data/adac/adac_kba_price_data.pkl')
    result.to_csv('data/adac/adac_kba_price_data.csv')
    
def get_aggregated_adac_price_data() -> pd.DataFrame:
    return pd.read_pickle('data/adac/adac_kba_price_data.pkl')


if __name__ == "__main__":
    pass
    #save_aggregated_price_data()