#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Import hhld expenditure data and adjust physical units 2001-2018

@author: lenakilian

Before this run:
    1. LCFS_PhysicalUnits_Flights.py
    2. LCFS_PhysicalUnits_Rent.py
    3. LCFS_import_data_function.py
    
Next run: LCFS_estimate_emissions.py
"""

import pandas as pd
import LCFS_import_data_function as lcfs_import
import copy as cp
import numpy as np

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

years = list(range(2001, 2020))
lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020']))

# Define function needed
def isNaN(string):
    return string != string

# Load physical unit data
# LCFS with physical units 
flights_og = pd.read_excel(wd + 'data/processed/LCFS/Controls/flights_2001-2018.xlsx', sheet_name=None, index_col = 'case')
rent_og = pd.read_excel(wd + 'data/processed/LCFS/Controls/rent_2001-2018.xlsx', sheet_name=None)

for year in years:
    rent_og[str(year)] = rent_og[str(year)].reset_index()
    rent_og[str(year)].columns = [x.lower() for x in rent_og[str(year)].columns]
    rent_og[str(year)] = rent_og[str(year)].set_index('case')

# Load LCFS data
lcfs = {}
for year in years:
    dvhh_file = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    dvper_file = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    
    lcfs[year] = lcfs_import.import_lcfs(year, dvhh_file, dvper_file).drop_duplicates()
    lcfs[year] = lcfs[year].reset_index()
    lcfs[year].columns = [x.lower() for x in lcfs[year].columns]
    lcfs[year] = lcfs[year].set_index('case')    

    
# add 2020 data
lcfs[2020] = pd.read_csv(wd + 'data/raw/LCFS/LCFS_aggregated_2020_adjusted.csv', index_col=[0], header=[0]).fillna(0)
# adjust income to LCFS by prop of income data
lcfs[2020].columns = [str(x) for x in lcfs[2020].columns]

years.append(2020)


# load CPI corrector data
# adjust to CPI
ref_year = 2007 # choose year which to adjust expenditure to
# import cpi cat lookup
cpi_lookup = pd.read_excel(wd + 'data/processed/CPI_lookup.xlsx', sheet_name='Sheet4')
cpi_lookup['ccp_lcfs'] = [x.split(' ')[0] for x in cpi_lookup['ccp_lcfs']]
# import cpi data --> uses 2015 as base year, change to 2007
cpi = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0)\
    .loc[[str(x) for x in years]].T.dropna(how='all').astype(float)
#check = cp.copy(cpi)
cpi = cpi.apply(lambda x: x/cpi[str(ref_year)] * 100)
cpi['Type'] = [x.split(' ')[0] + ' ' + x.split(' ')[1] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Type'].isin(['CPI INDEX']) == True]
cpi['Reference_year'] = [x[-8:] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Reference_year'].str.contains('=100') == True]
cpi['Product'] = [x.replace('CPI INDEX ', '').split(' ')[0] for x in cpi.index.tolist()]

# extract inflation data
# import cpi data --> uses 2015 as base year, change to 2007
inflation = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0).loc[[str(x) for x in years], 'CPI INDEX 00: ALL ITEMS 2015=100']\
        .T.dropna(how='all').astype(float)
# extract 2020 relative to 2019, to adjust non-cpi data to 2020 income, not keep it as 2019
inflation_2020 = inflation['2020']/inflation['2019']

###########
# Regular #
###########
hhdspend = {}

for year in years:
    hhdspend[year] = cp.copy(lcfs[year])
    
    # save order of coicop cats    
    order = hhdspend[year].columns.tolist()
    
    if year != 2020:
    # adjust to physical units
    # flights
        flights = cp.copy(flights_og[str(year)][['7.3.4.1_proxy', '7.3.4.2_proxy']])
        flights = flights.rename(columns={'7.3.4.1_proxy':'7.3.4.1', '7.3.4.2_proxy':'7.3.4.2'})
        hhdspend[year] = hhdspend[year].drop(['7.3.4.1', '7.3.4.2'], axis = 1).join(flights[['7.3.4.1', '7.3.4.2']])
        
        # rent
        rent = cp.copy(rent_og[str(year)])
        rent = rent.rename(columns={'4.1.1_proxy':'4.1.1', '4.1.2_proxy':'4.1.2'})
        hhdspend[year] = hhdspend[year].drop(['4.1.1', '4.1.2'], axis = 1).join(rent[['4.1.1', '4.1.2']])

        hhdspend[year] = hhdspend[year][order]
        
    else:
        for item in hhdspend[year].loc[:,'1.1.1.1':'12.5.3.5'].columns:
            temp = hhdspend[year][[item, 'weight']].join(lcfs[year][['group_var']]).set_index('group_var', append=True)
            temp[item] = temp[item] * temp['weight']
            temp = temp.join(temp.sum(axis=0, level=1), rsuffix='_sum')
            temp[item] = temp[item] / temp[item + '_sum'] * temp.loc[('all', 'All'), item + '_sum']
            temp[item] = temp[item] / temp['weight']
            
            hhdspend[year] = hhdspend[year].drop(item, axis=1).join(temp.reset_index(level=1)[[item]])
            
        # add demo data from 2019
        temp = pd.DataFrame(index = ['all', 
                                     '18-29', '30-49', '50-64', '65-74', '75+', 
                                     'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])
        temp['weight'] = [27806.69625, 
                          2481.955052, 9283.447752, 7806.285708, 5866.098217, 2368.909522, 
                          2722.732542, 2580.059263, 2604.357674, 2656.320339, 2782.599699, 2771.268831, 2787.92701, 2973.838045, 2950.431388, 2977.161461]
        temp['no people'] = [2.361078369, 
                             2.395053135, 3.000146549, 2.359156424, 1.70851027, 1.443336229, 
                             2.513119227, 2.487091772, 2.439497585, 2.313288151, 2.366138697, 2.447083911, 2.290871663, 2.385522909, 2.370183064, 2.034382869]
        temp['hhld_oecd_equ'] = [1.688811468, 
                                 1.733913468, 2.049922225, 1.758839035, 1.284292486, 0.997353608, 
                                 1.737299662, 1.754530487, 1.723708663, 1.625004594, 1.680208678, 1.778676115, 1.673063444, 1.739808114, 1.734837822, 1.456502052]
        temp['hhld_oecd_mod'] = [1.481853604, 
                                 1.513532565, 1.699620847, 1.541904063, 1.225403118, 1.032421542, 
                                 1.505082547, 1.518505583, 1.499190431, 1.437895926, 1.478035987, 1.544683153, 1.477080103, 1.521605193, 1.516818963, 1.328096309]
        
        hhdspend[year] = temp.join(hhdspend[year][order].drop(['weight', 'no people'], axis=1))
        
        hhdspend[year]['income anonymised'] = hhdspend[year]['income anonymised'] * inflation_2020
            
    hhdspend[year].index.name = 'case'
    hhdspend[year] = hhdspend[year].reset_index()
    
    hhdspend[year].to_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv')
    
    print('Year ' + str(year) + ' completed')

###################
# Adjusted to CPI #
###################
# Adjust everything to 2007 prices, to be used with 2007 multipliers 
inflation = inflation.apply(lambda x: x/inflation[str(ref_year)])

# import gas and electricity data to adjust to this - use physical unit
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
    [['Electricity', 'Natural gas']].dropna(how='all').astype(float).drop_duplicates()

hhdspend_cpi = {}

flights_ref_year = cp.copy(flights_og[str(ref_year)])

cpi_years = cp.copy(years)
cpi_years.remove(ref_year)
for year in [ref_year] + cpi_years: # need to run ref_year first, to have the data to be used in next iteratino(s)
    hhdspend_cpi[year] = cp.copy(hhdspend[year]).set_index('case')
    
    order = hhdspend_cpi[year].columns.tolist()
    # adjust income
    
    hhdspend_cpi[year]['income anonymised'] = hhdspend_cpi[year]['income anonymised'] / inflation[str(year)]
    if year != 2020:
        # adjust expenditure by CPI - do thise before adjusting for physical data for flights and rent
        if ref_year <= 2014 or year <= 2014: # befroe 2015 we only have index level 3
            cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP3_index']))
        else:
            cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP4_index']))
        
        for item in hhdspend_cpi[year].loc[:,'1.1.1.1':'12.5.3.5'].columns:
            hhdspend_cpi[year][item] = hhdspend_cpi[year][item] * (100 / float(cpi.loc[cpi_dict[item], str(year)])) # adjust to cpi
        
        # adjust gas (4.4.2) and electricity (4.4.1) to kwh ratio
        # generate multiplier compared to 2007
        multiplier = gas_elec.loc[year] / gas_elec.loc[ref_year]
        
        # adjust totals to new total
        temp = hhdspend_cpi[year][['4.4.1', '4.4.2']].apply(lambda x: x*hhdspend_cpi[year]['weight'])
        # get weighted sums of ref year
        total_spend_ry_elec = np.sum(hhdspend_cpi[ref_year]['4.4.1'] * hhdspend_cpi[ref_year]['weight'])
        total_spend_ry_gas = np.sum(hhdspend_cpi[ref_year]['4.4.2'] * hhdspend_cpi[ref_year]['weight'])
        # calculate new totals
        total_spend_new_elec = total_spend_ry_elec * multiplier['Electricity']
        total_spend_new_gas = total_spend_ry_gas * multiplier['Natural gas']
        # estimate new gas and elec exp. adjusted to consumption proportions
        temp['4.4.1'] = (temp['4.4.1'] / temp['4.4.1'].sum()) * total_spend_new_elec 
        temp['4.4.2'] = (temp['4.4.2'] / temp['4.4.2'].sum()) * total_spend_new_gas
        temp = temp.apply(lambda x: x/hhdspend_cpi[year]['weight'])
        hhdspend_cpi[year] = hhdspend_cpi[year].drop(['4.4.1', '4.4.2'], axis=1).join(temp[['4.4.1', '4.4.2']])
        
        # adjust flights by number of flights
        flight_multipliers = flights_og[str(year)][['Domestic', 'International']].join(hhdspend[year].set_index('case')[['weight']])
        flight_multipliers[['Domestic', 'International']] = flight_multipliers[['Domestic', 'International']].apply(lambda x:x* flight_multipliers['weight'])
        
        temp = flights_og[str(ref_year)][['Domestic', 'International']].join(hhdspend[ref_year].set_index('case')[['weight']])
        temp[['Domestic', 'International']] = temp[['Domestic', 'International']].apply(lambda x:x* temp['weight'])
        
        flight_multipliers = flight_multipliers.sum(axis=0).reset_index().rename(columns={0:'year'}).set_index('index')\
            .join(temp.sum(axis=0).reset_index().rename(columns={0:'ref_year'}).set_index('index'))
            
        flight_multipliers['multipliers'] = flight_multipliers['year'] / flight_multipliers['ref_year']
        
        flights_ref = hhdspend[ref_year].set_index('case')[['7.3.4.1', '7.3.4.2', 'weight']]
        flights_ref = flights_ref[['7.3.4.1', '7.3.4.2']].apply(lambda x: x* flights_ref['weight']).sum(axis=0)
        
        flights_yr = hhdspend[year].set_index('case')[['7.3.4.1', '7.3.4.2', 'weight']]
        flights_yr[['7.3.4.1', '7.3.4.2']] = flights_yr[['7.3.4.1', '7.3.4.2']].apply(lambda x: x* flights_yr['weight'])
        
        flights_yr['7.3.4.1'] = (flights_yr['7.3.4.1']/flights_yr['7.3.4.1'].sum()) * (flights_ref['7.3.4.1'] * flight_multipliers.loc['Domestic', 'multipliers'])
        flights_yr['7.3.4.2'] = (flights_yr['7.3.4.2']/flights_yr['7.3.4.2'].sum()) * (flights_ref['7.3.4.2'] * flight_multipliers.loc['International', 'multipliers'])
        
        flights_yr[['7.3.4.1', '7.3.4.2']] = flights_yr[['7.3.4.1', '7.3.4.2']].apply(lambda x: x/ flights_yr['weight'])
        
        hhdspend_cpi[year] = hhdspend_cpi[year].drop(['7.3.4.1', '7.3.4.2'], axis=1).join(flights_yr[['7.3.4.1', '7.3.4.2']])
    
    else:
        if ref_year <= 2014 or year <= 2014: # befroe 2015 we only have index level 3
            cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP3_index']))
        else:
            cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP4_index']))
        
        for item in hhdspend_cpi[year].loc[:,'1.1.1.1':'12.5.3.5'].columns:
            hhdspend_cpi[year][item] = hhdspend_cpi[year][item] * (100 / float(cpi.loc[cpi_dict[item], '2019'])) # adjust to cpi
    
        temp = hhdspend_cpi[year].set_index('group_var', append=True)[['weight', '4.4.1', '4.4.2']].swaplevel(axis=0)
        temp[['4.4.1', '4.4.2']] = temp[['4.4.1', '4.4.2']].apply(lambda x: x*temp['weight'])
        temp = temp.join(temp.sum(axis=0, level=0), rsuffix='_sum')
        # get weighted sums of ref year
        total_spend_ry_elec = np.sum(hhdspend_cpi[ref_year]['4.4.1'] * hhdspend_cpi[ref_year]['weight'])
        total_spend_ry_gas = np.sum(hhdspend_cpi[ref_year]['4.4.2'] * hhdspend_cpi[ref_year]['weight'])
        # calculate new totals
        total_spend_new_elec = total_spend_ry_elec * multiplier['Electricity']
        total_spend_new_gas = total_spend_ry_gas * multiplier['Natural gas']
        # estimate new gas and elec exp. adjusted to consumption proportions
        temp['4.4.1'] = temp['4.4.1'] / temp['4.4.1_sum'] * total_spend_new_elec
        temp['4.4.2'] = temp['4.4.2'] / temp['4.4.2_sum'] * total_spend_new_gas
        temp[['4.4.1', '4.4.2']] = temp[['4.4.1', '4.4.2']].apply(lambda x: x/temp['weight'])
        hhdspend_cpi[year] = hhdspend_cpi[year].drop(['4.4.1', '4.4.2'], axis=1).join(temp[['4.4.1', '4.4.2']].droplevel(axis=0, level=0))   
        
    # clean data
    hhdspend_cpi[year] = hhdspend_cpi[year][order]
    hhdspend_cpi[year].index.name = 'case'
    hhdspend_cpi[year] = hhdspend_cpi[year].reset_index()
    
    hhdspend_cpi[year].to_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '_wCPI_ref' + str(ref_year) + '.csv')
    
    print('Year ' + str(year) + ' with CPI completed')