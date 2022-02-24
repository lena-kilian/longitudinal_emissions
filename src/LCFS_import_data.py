#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

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

# LCFS with physical units 
flights = pd.read_excel(wd + 'data/processed/LCFS/Controls/flights_2001-2018.xlsx', sheet_name=None)
rent = pd.read_excel(wd + 'data/processed/LCFS/Controls/rent_2001-2018.xlsx', sheet_name=None)
        
for year in years:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    hhdspend[year] = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    
    # adjust to physical units
    # flights
    flights[str(year)].columns = [x.lower() for x in flights[str(year)].columns]
    if 'case' in flights[str(year)].columns:
        flights[str(year)] = flights[str(year)].set_index('case')
    hhdspend[year]['7.3.4.1'] = flights[str(year)]['domestic'] / flights[str(year)]['domestic'].sum() * hhdspend[year]['7.3.4.1'].sum()
    hhdspend[year]['7.3.4.2'] = flights[str(year)]['international'] / flights[str(year)]['international'].sum() * hhdspend[year]['7.3.4.2'].sum()
    # rent
    rent[str(year)].columns = [x.lower() for x in rent[str(year)].columns]
    if 'case' in rent[str(year)].columns:
        rent[str(year)] = rent[str(year)].set_index('case')
    hhdspend[year]['4.1.1'] = rent[str(year)]['4.1.1_proxy']
    hhdspend[year]['4.1.2'] = rent[str(year)]['4.1.2_proxy']
    
    hhdspend[year].index.name = 'case'
    hhdspend[year] = hhdspend[year].reset_index()
    
    hhdspend[year].to_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv')
    
    print('Year ' + str(year) + ' completed')

for year in years:
    print(str(year))
    print(flights[str(year)].columns)
    print(rent[str(year)].columns)