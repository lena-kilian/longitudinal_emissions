#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Import hhld expenditure data, adjust physical units, adjust CPI, 2019 & 2020

@author: lenakilian
"""


###### TO DO
# Base cpi on 2019 data, the use 2019 multipliers for 2020 data .
# Rerun entire analysis with corrected data


# make sure to use per capita data

import pandas as pd
import LCFS_import_data_function as lcfs_import
import copy as cp
import pickle

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

years = [2019, 2020]
lcf_years = dict(zip(years, ['2019-2020', '2009']))

def isNaN(string):
    return string != string

# load LFC data
hhdspend = {}


# adjust to CPI
# import cpi cat lookup
cpi_lookup = pd.read_excel(wd + 'data/processed/CPI_lookup.xlsx', sheet_name='Sheet4')
cpi_lookup['ccp_lcfs'] = [x.split(' ')[0] for x in cpi_lookup['ccp_lcfs']]
# import cpi data --> uses 2015 as base year, change to 2007
cpi = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0)\
    .loc[[str(x) for x in years + [2015]]].T.dropna(how='all').astype(float)
#check = cp.copy(cpi)
cpi = cpi.apply(lambda x: x/cpi[str(years[0])] * 100)
cpi['Type'] = [x.split(' ')[0] + ' ' + x.split(' ')[1] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Type'].isin(['CPI INDEX']) == True]
cpi['Reference_year'] = [x[-8:] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Reference_year'].str.contains('=100') == True]
cpi['Product'] = [x.replace('CPI INDEX ', '').split(' ')[0] for x in cpi.index.tolist()]

# import gas and electricity data to adjust to this
gas_elec = pd.read_excel(wd + 'data/raw/Energy_Use/Energy Consumption in the UK (ECUK) 2021.xlsx', 
                         sheet_name='Table C1', skiprows=4, nrows=53).T
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
for year in years:
    if year == 2019:
        file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
        file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
        hhdspend[year] = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
        hhdspend[year] = hhdspend[year].reset_index()
        hhdspend[year].columns = [x.lower() for x in hhdspend[year].columns]
        hhdspend[year] = hhdspend[year].set_index('case')
    else:
        temp = pd.read_excel(wd + 'data/raw/Expenditure/processed_201920.xlsx').set_index('Coicop')[['Multiplier_2020_T']]
        temp.index = [str(x) for x in temp.index]
        
        hhdspend[year] = hhdspend[2019].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x:x*hhdspend[2019]['weight']).sum(0)
        hhdspend[year] = hhdspend[year] / (hhdspend[2019]['no people'] * hhdspend[2019]['weight']).sum()
        hhdspend[year].index = [str(x) for x in hhdspend[year].index]
        
        hhdspend[year] = temp.join(pd.DataFrame(hhdspend[year]), how='right').rename(columns={0:'all'})
        hhdspend[year]['pc_exp'] = hhdspend[year]['all'] * hhdspend[year]['Multiplier_2020_T']
        hhdspend[year] = hhdspend[year][['pc_exp']].T
    
    # save order of coicop cats    
    order = hhdspend[year].columns.tolist()

    # adjust expenditure by CPI - do thise before adjusting for physical data for flights and rent
    if year <= 2014:
        cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP3_index']))
    else:
        cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP4_index']))
    
    for item in hhdspend[year].loc[:,'1.1.1.1':'12.5.3.5'].columns:
        hhdspend[year][item] = hhdspend[year][item] * (float(cpi.loc[cpi_dict[str(item)], str(year)]) / 100)
        
    # adjust gas (4.4.2) and electricity (4.4.1) to kwh ratio
    # generate multiplier compared to 2007
    multiplier = gas_elec.loc[year] / gas_elec.loc[years[0]]
    pc_spend_new_elec = ((hhdspend[2019]['4.4.1'] * hhdspend[2019]['weight']).sum() / 
                         (hhdspend[2019]['weight'] * hhdspend[2019]['no people']).sum())
    pc_spend_new_gas = ((hhdspend[2019]['4.4.2'] * hhdspend[2019]['weight']).sum() / 
                        (hhdspend[2019]['weight'] * hhdspend[2019]['no people']).sum())
    
    # adjust totals to new total
    hhdspend[year]['4.4.1'] = (hhdspend[year]['4.4.1'] / hhdspend[year]['4.4.1'].sum()) * (pc_spend_new_elec * multiplier['Electricity'])
    hhdspend[year]['4.4.2'] = (hhdspend[year]['4.4.2'] / hhdspend[year]['4.4.2'].sum()) * (pc_spend_new_gas * multiplier['Natural gas'])
    hhdspend[year] = hhdspend[year][order]
    
    hhdspend[year].index.name = 'case'
    hhdspend[year] = hhdspend[year].reset_index()
    
    hhdspend[year].to_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '_wCPI.csv')
    
    print('Year ' + str(year) + ' completed')
    