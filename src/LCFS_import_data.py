#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""


###### TO DO
# Base cpi on 2007 data, the use 2007 multipliers for 2008 and 2009 data .
# Rerun entire analysis with corrected data


import pandas as pd
import LCFS_import_data_function as lcfs_import
import copy as cp
import pickle

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

years = list(range(2001, 2019))
lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))

# load LFC data
hhdspend = {}

"""
# adjust to CPI
cpi_lookup = pd.read_excel(wd + 'data/processed/CPI_lookup.xlsx', sheet_name='Sheet4')
cpi_lookup['ccp_lcfs'] = [x.split(' ')[0] for x in cpi_lookup['ccp_lcfs']]
cpi = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0).loc[[str(x) for x in years]].T.dropna(how='all')
cpi['Type'] = [x.split(' ')[0] + ' ' + x.split(' ')[1] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Type'].isin(['CPI INDEX']) == True]
cpi['Reference_year'] = [x[-8:] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Reference_year'].str.contains('=100') == True]
cpi['Product'] = [x.replace('CPI INDEX ', '').split(' ')[0] for x in cpi.index.tolist()]
"""

# LCFS with physical units 
flights = pd.read_excel(wd + 'data/processed/LCFS/Controls/flights_2001-2018.xlsx', sheet_name=None, index_col = 'case')
rent = pd.read_excel(wd + 'data/processed/LCFS/Controls/rent_2001-2018.xlsx', sheet_name=None)
for year in years:
    rent[str(year)] = rent[str(year)].reset_index()
    rent[str(year)].columns = [x.lower() for x in rent[str(year)].columns]
    rent[str(year)] = rent[str(year)].set_index('case')
        
for year in years:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    hhdspend[year] = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    hhdspend[year] = hhdspend[year].reset_index()
    hhdspend[year].columns = [x.lower() for x in hhdspend[year].columns]
    hhdspend[year] = hhdspend[year].set_index('case')
    
    """
    # adjust expenditure by CPI
    if year <= 2014:
        cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP3_index']))
    else:
        cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP4_index']))
    
    for item in hhdspend[year].loc[:,'1.1.1.1':'12.5.3.5'].columns:
        hhdspend[year][item] = hhdspend[year][item] * (float(cpi.loc[cpi_dict[item], str(year)]) / 100)
    """
        
    # save order of coicop cats    
    order = hhdspend[year].columns.tolist()
    
    # adjust to physical units
    # flights
    flights[str(year)] = flights[str(year)].rename(columns={'7.3.4.1_proxy':'7.3.4.1', '7.3.4.2_proxy':'7.3.4.2'})
    hhdspend[year] = hhdspend[year].drop(['7.3.4.1', '7.3.4.2'], axis = 1).join(flights[str(year)][['7.3.4.1', '7.3.4.2']])
    
    # rent
    rent[str(year)] = rent[str(year)].rename(columns={'4.1.1_proxy':'4.1.1', '4.1.2_proxy':'4.1.2'})
    hhdspend[year] = hhdspend[year].drop(['4.1.1', '4.1.2'], axis = 1).join(rent[str(year)][['4.1.1', '4.1.2']])

    
    hhdspend[year] = hhdspend[year][order]
    
    hhdspend[year].index.name = 'case'
    hhdspend[year] = hhdspend[year].reset_index()
    
    hhdspend[year].to_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv')
    
    print('Year ' + str(year) + ' completed')

for year in years:
    print(str(year))
    print(flights[str(year)].columns)
    print(rent[str(year)].columns)