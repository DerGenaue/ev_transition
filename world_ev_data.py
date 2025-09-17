"""
Provides data from all sources in a homogeneous format
Date is always the start date of a time span,
so eg. average 2024 data is reported as 2024-01-01
not all columns are always available, but the naming and the format is consistent
"""


from enum import StrEnum

import pandas as pd
import numpy as np

from owid_datagrabber import owid_electric_car_sales


class EntityType(StrEnum):
    Country = "Country"
    CountryAlt = "CountryAlt"
    Group = "Group"
    World = "World"

ENTITY = "entity"
ENTITY_TYPE = "entity_type"
STOCK_SHARE_EVS = "stock_share_evs"
STOCK_SHARE_BEVS = "stock_share_bevs"
STOCK_SHARE_PHEVS = "stock_share_phevs"
STOCK_SHARE_FCEVS = "stock_share_fcevs"
STOCK_SHARE_ICE = "stock_share_ice"
STOCK_EVS = "stock_evs"
STOCK_BEVS = "stock_bevs"
STOCK_PHEVS = "stock_phevs"
STOCK_FCEVS = "stock_fcevs"
STOCK_ICE = "stock_ice"
STOCK_TOTAL = "stock_total"
SALES_SHARE_EVS = "sales_share_evs"
SALES_SHARE_BEVS = "sales_share_bevs"
SALES_SHARE_PHEVS = "sales_share_phevs"
SALES_SHARE_FCEVS = "sales_share_fcevs"
SALES_SHARE_ICE = "sales_share_ice"
SALES_EVS = "sales_evs"
SALES_BEVS = "sales_bevs"
SALES_PHEVS = "sales_phevs"
SALES_FCEVS = "sales_fcevs"
SALES_ICE = "sales_ice"
SALES_TOTAL = "sales_total"


def robbie_andrew_data(subsume_zev_into_bev=True, drop_before_year='2005') -> pd.DataFrame:
    data = pd.read_csv('data/robbieandrew/all_carsales_monthly.csv', index_col=['Country', 'YYYYMM', 'Fuel'], parse_dates=['YYYYMM'], date_format={'YYYYMM': '%Y%m'})
    data = data['Value'].unstack(level='Fuel').rename_axis(None, axis=1)
    data.rename(columns={
        'BatteryElectric': SALES_BEVS,
        'PluginHybrid': SALES_PHEVS,
    }, inplace=True)
    data[SALES_TOTAL] = data[list(data.columns)].sum(axis=1)
    # Some rows do not contain data
    data.drop(data[data[SALES_TOTAL] == 0].index, inplace=True)
    # Crop to only relevant years
    data.drop(data[data.index.get_level_values(1) < drop_before_year].index, inplace=True)
    
    # Merge columns
    data[SALES_PHEVS] += data['Plug_inHybrid'].fillna(0)
    data.drop(columns=['Plug_inHybrid'], inplace=True)
    
    # some countries only give ZEV data
    if subsume_zev_into_bev:
        data[SALES_BEVS] += data['ZEV'].fillna(0)
        data.drop(columns=['ZEV'], inplace=True)
    
    # Calculate shares from absolute numbers
    # BEV and EV share are guaranteed to always be available
    data[SALES_SHARE_BEVS] = data[SALES_BEVS].fillna(0) / data[SALES_TOTAL]
    data[SALES_SHARE_PHEVS] = data[SALES_PHEVS] / data[SALES_TOTAL]
    data[SALES_SHARE_EVS] = (data[SALES_BEVS].fillna(0) + data[SALES_PHEVS].fillna(0)) / data[SALES_TOTAL]
    
    data[ENTITY_TYPE] = EntityType.Country
    data.loc[data.index.get_level_values(0).isin(['EFTA', 'EU + EFTA + UK', 'EUROPEAN UNION']), ENTITY_TYPE] = EntityType.Group
    data.loc[data.index.get_level_values(0).isin(['California CNCDA', 'United Kingdom SMMT']), ENTITY_TYPE] = EntityType.CountryAlt
    
    return data

def iea_data() -> pd.DataFrame:
    data = pd.read_excel(f"data/iea/EVDataExplorer2025.xlsx", sheet_name="GEVO_EV_2025")
    data = data.loc[
        (data['category'] == 'Historical') &
        (data['mode'] == 'Cars') &
        (data['parameter'].isin(['EV sales', 'EV sales share', 'EV stock', 'EV stock share']))
    ]
    data.drop(columns=['category', 'mode', 'unit'], inplace=True)
    data.set_index(['region_country', 'year', 'parameter', 'powertrain'], inplace=True)
    entity_to_agg = data['Aggregate group'].groupby('region_country').max()
    data.drop(columns=['Aggregate group'], inplace=True)
    data = data.unstack(level=['powertrain', 'parameter'])
    data.columns = data.columns.to_flat_index()

    data.rename(columns={
        ('value', 'BEV', 'EV stock'): STOCK_BEVS,
        ('value', 'PHEV', 'EV stock'): STOCK_PHEVS,
        ('value', 'FCEV', 'EV stock'): STOCK_FCEVS,
        ('value', 'BEV', 'EV sales'): SALES_BEVS,
        ('value', 'PHEV', 'EV sales'): SALES_PHEVS,
        ('value', 'FCEV', 'EV sales'): SALES_FCEVS,
        ('value', 'EV', 'EV sales share'): SALES_SHARE_EVS,
        ('value', 'EV', 'EV stock share'): STOCK_SHARE_EVS,
    }, inplace=True)
    
    # numbers are given in percent, convert to fraction
    data[STOCK_SHARE_EVS] /= 100
    data[SALES_SHARE_EVS] /= 100

    # calculate total numbers from the partial data we are given
    data_0 = data.fillna(0)
    data[SALES_TOTAL] = (data_0[SALES_BEVS] + data_0[SALES_PHEVS] + data_0[SALES_FCEVS]) / data_0[SALES_SHARE_EVS]
    data[SALES_SHARE_BEVS] = data_0[SALES_BEVS] / data[SALES_TOTAL]

    data[ENTITY_TYPE] = EntityType.Group
    data.loc[data.index.get_level_values(0).isin(entity_to_agg.loc[entity_to_agg == 'Other'].index), ENTITY_TYPE] = EntityType.Country
    data.loc[data.index.get_level_values(0).isin(['World']), ENTITY_TYPE] = EntityType.World
    
    return data

def owid_data() -> pd.DataFrame:
    data = owid_electric_car_sales()
    data.rename(columns={
        'ev_sales_share': SALES_SHARE_EVS,
        'ev_stock_share': STOCK_SHARE_EVS,
        'bev_sales': SALES_BEVS,
        'bev_stock': STOCK_BEVS,
        'phev_sales': SALES_PHEVS,
        'phev_stock': STOCK_PHEVS,
        'ev_sales': SALES_EVS,
        #'bev_share_ev_cars': ,
        #'phev_share_ev_cars': ,
        'bev_share_car_sales': SALES_SHARE_BEVS,
        'phev_share_car_sales': SALES_SHARE_PHEVS,
        'ev_stock': STOCK_EVS,
        'total_cars_sold': SALES_TOTAL,
        'non_ev_cars_sold': ENTITY_TYPE,
    }, inplace=True)

    # numbers are given in percent, convert to fraction
    data[STOCK_SHARE_EVS] /= 100
    data[SALES_SHARE_EVS] /= 100
    data[SALES_SHARE_BEVS] /= 100
    data[SALES_SHARE_PHEVS] /= 100

    data[ENTITY_TYPE] = EntityType.Country
    data.loc[data.index.get_level_values(0).isin(['European Union (27)', 'Europe']), ENTITY_TYPE] = EntityType.Group
    data.loc[data.index.get_level_values(0).isin(['World']), ENTITY_TYPE] = EntityType.World
    
    return data

def extra_data() -> pd.DataFrame:
    
    # Manually collected data on Vietnam
    data_vietnam = pd.read_csv('data/vietnam/vietnam_ev_sales_share.csv')
    data_vietnam.rename(columns={
        'bev_sales_share': SALES_SHARE_BEVS
    }, inplace=True)
    # There are apparently no relevant numbers of PHEVs in Vietnam so far
    data_vietnam[SALES_SHARE_BEVS] /= 100
    data_vietnam[SALES_SHARE_PHEVS] = 0#
    data_vietnam[SALES_SHARE_EVS] = data_vietnam[SALES_SHARE_BEVS]
    
    data_vietnam['Country'] = 'Vietnam'
    data_vietnam[ENTITY_TYPE] = EntityType.Country
    data_vietnam.set_index(['Country', 'YYYYMM'], inplace=True)
    
    return data_vietnam

def merge_all_ev_data(interpolate=True):
    """Merges all data sources into one dataframe"""
    
    owid_car_sales = owid_data()
    robbie_andrew_car_sales = robbie_andrew_data()
    iea_car_sales = iea_data()
    extra_car_sales = extra_data()
    
    # Take Robbie Andrew's data as base,
    # then fill it with IEA and OWID data
    # and use the extra data to add / update more current data
    
    # TODO: make sure all dates have the same format and are parsed correctly
    # TODO: implement merging of data
    
    print('Hello')


if __name__ == "__main__":
    merge_all_ev_data()