#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Import hhld expenditure data, adjust physical units, adjust CPI, 2007 & 2009 AND 2019 & 2020

@author: lenakilian
"""


###### TO DO
# Base cpi on 2007 data, the use 2007 multipliers for 2008 and 2009 data .
# Rerun entire analysis with corrected data


import pandas as pd
import LCFS_import_data_function as lcfs_import
from sys import platform

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'

all_years = [2007, 2009, 2019, 2020]
lcf_years = dict(zip(all_years, ['2007', '2009', '2019-2020', '2020-2021']))

def isNaN(string):
    return string != string

for years in [[2007, 2009], [2019, 2020]]:
    # load LFC data
    hhdspend = {}
    
    y1 = years[0]
    
    # adjust to CPI
    # import cpi cat lookup
    cpi_lookup = pd.read_excel(wd + 'data/processed/CPI_lookup.xlsx', sheet_name='Sheet4')
    cpi_lookup['ccp_lcfs'] = [x.split(' ')[0] for x in cpi_lookup['ccp_lcfs']]
    # import cpi data --> uses 2015 as base year, change to y1
    cpi = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0)\
        .loc[[str(x) for x in years + [2015]]].T.dropna(how='all').astype(float)
    #check = cp.copy(cpi)
    cpi = cpi.apply(lambda x: x/cpi[str(y1)] * 100)
    cpi['Type'] = [x.split(' ')[0] + ' ' + x.split(' ')[1] for x in cpi.index.tolist()]
    cpi = cpi.loc[cpi['Type'].isin(['CPI INDEX']) == True]
    cpi['Reference_year'] = [x[-8:] for x in cpi.index.tolist()]
    cpi = cpi.loc[cpi['Reference_year'].str.contains('=100') == True]
    cpi['Product'] = [x.replace('CPI INDEX ', '').split(' ')[0] for x in cpi.index.tolist()]
    
    
    # import gas and electricity data to adjust to this
    gas_elec = pd.read_excel(wd + 'data/raw/Energy_Use/Energy Consumption in the UK (ECUK) 2021.xlsx', 
                             sheet_name='Table C1', skiprows=4).T
    index = []
    for i in range(len(gas_elec[0])):
        if isNaN(gas_elec[0][i]) == False:
            index.append(gas_elec[0][i])
        else: 
            index.append(index[i-1])
            
    gas_elec[0] = index
    gas_elec = gas_elec.set_index([0, 1]).loc['Domestic'].T.set_index('Year').rename(columns={'Natural gas\n[Note 8]':'Natural gas'})\
        [['Electricity', 'Natural gas']].dropna(how='all').astype(float)
    
      
    # LCFS with physical units 
    flights = pd.read_excel(wd + 'data/processed/LCFS/Controls/flights_2001-2020.xlsx', sheet_name=None, index_col = 'case')
    rent = pd.read_excel(wd + 'data/processed/LCFS/Controls/rent_2001-2020.xlsx', sheet_name=None)
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
        
        # save order of coicop cats    
        order = hhdspend[year].columns.tolist()
    
        # adjust expenditure by CPI - do thise before adjusting for physical data for flights and rent
        if year <= 2014:
            cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP3_index']))
        else:
            cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP4_index']))
        
        for item in hhdspend[year].loc[:,'1.1.1.1':'12.5.3.5'].columns:
            hhdspend[year][item] = hhdspend[year][item] * (float(cpi.loc[cpi_dict[item], str(year)]) / 100)
        
        # adjust to physical units
        # flights
        flights[str(year)] = flights[str(year)].join(hhdspend[year][['7.3.4.1', '7.3.4.2']])
        for item in ['7.3.4.1', '7.3.4.2']:
            total_proxy = flights[str(year)][item + '_proxy'].sum()
            flights[str(year)][item] = (flights[str(year)][item + '_proxy'] /  total_proxy) * flights[str(year)][item].sum()
        hhdspend[year] = hhdspend[year].drop(['7.3.4.1', '7.3.4.2'], axis = 1).join(flights[str(year)][['7.3.4.1', '7.3.4.2']])
        
        # rent
        rent[str(year)] = rent[str(year)].join(hhdspend[year][['4.1.1', '4.1.2']])
        for item in ['4.1.1', '4.1.2']:
            total_proxy = rent[str(year)][item + '_proxy'].sum()
            rent[str(year)][item] = (rent[str(year)][item + '_proxy'] /  total_proxy) * rent[str(year)][item].sum()
        hhdspend[year] = hhdspend[year].drop(['4.1.1', '4.1.2'], axis = 1).join(rent[str(year)][['4.1.1', '4.1.2']])
        
        # adjust gas (4.4.2) and electricity (4.4.1) to kwh ratio
        # generate multiplier compared to y1
        gas_elec = gas_elec.mean(axis=0, level=0)
        multiplier = gas_elec.loc[year] / gas_elec.loc[y1]
        total_spend_new_elec = hhdspend[y1]['4.4.1'].sum() * multiplier['Electricity']
        total_spend_new_gas = hhdspend[y1]['4.4.2'].sum() * multiplier['Natural gas']
        
        # adjust totals to new total
        hhdspend[year]['4.4.1'] = (hhdspend[year]['4.4.1'] / hhdspend[year]['4.4.1'].sum()) * total_spend_new_elec 
        hhdspend[year]['4.4.2'] = (hhdspend[year]['4.4.2'] / hhdspend[year]['4.4.2'].sum()) * total_spend_new_gas
        hhdspend[year] = hhdspend[year][order]
        
        hhdspend[year].index.name = 'case'
        hhdspend[year] = hhdspend[year].reset_index()
        
        hhdspend[year].to_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '_wCPI.csv')
        
        print('Year ' + str(year) + ' completed')
    
    for year in years:
        print(str(year))
        print(flights[str(year)].columns)
        print(rent[str(year)].columns)
        