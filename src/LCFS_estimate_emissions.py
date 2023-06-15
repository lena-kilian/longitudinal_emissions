#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian

Before this run:
    1. LCFS_import_data_function.py
    2. LCFS_import_data.py
    
Next run: 
    - emissions_summary.py
"""

import pandas as pd
import estimate_emissions_main_function_2021 as estimate_emissions
import copy as cp
import mapclassify as ps
import pickle
from sys import platform

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'

years = list(range(2001, 2021))
lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020',
                             '2020-2021']))


ref_year = 2008 # choose year which expenditure is adjusted to (by CPI)

hhd_type_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp3_lookup.xlsx', sheet_name='hhd_type')

years = list(range(2001, 2021))
pop = 'hhld_oecd_mod' #'no people' # change this to oecd equivalised scale if needed  #

# load LFC data
lcfs = {}
people = {}

for year in years:
    # regular
    lcfs[year] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv').set_index('case')
    order = lcfs[year].columns
    # with cpi
    lcfs[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '_wCPI_ref' + str(ref_year) + '.csv')\
        .set_index('case')[order]

lcfs['2020_2019cpi'] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_2020_wCPI_ref2019.csv').set_index('case')[order]

for year in list(lcfs.keys()):
    # separate sociodemographic variables
    people[year] = lcfs[year].loc[:,:'1.1.1.1'].iloc[:,:-1]
    
    # classify age range of hrp
    people[year]['age_group_hrp'] = 'Other'
    for i in [[18, 29], [30, 49], [50, 64], [65, 74]]:
        people[year].loc[people[year]['age hrp'] >= i[0], 'age_group_hrp'] = str(i[0]) + '-' + str(i[1])
    people[year].loc[people[year]['age hrp'] >= 80, 'age_group_hrp'] = '75+'
    
    # OECD household equivalent scales
    # https://www.oecd.org/economy/growth/OECD-Note-EquivalenceScales.pdf
    temp = cp.copy(people[year])
    temp['18+'] = temp['no people'] - temp['people aged <18']
    temp['hhld_oecd_mod'] = 0
    temp.loc[temp['18+'] > 0, '18+'] = temp['18+'] - 1
    temp.loc[temp['18+'] == 0, 'people aged <18'] = temp['people aged <18'] - 1
    temp['hhld_oecd_equ'] = temp['hhld_oecd_mod']
    # OECD-modified scale
    temp['hhld_oecd_mod'] = 1 + (temp['18+'] * 0.5) + (temp['people aged <18'] * 0.3)
    people[year] = people[year].join(temp[['hhld_oecd_mod']])
    # OECD equivalence scale
    temp['hhld_oecd_equ'] = 1 + (temp['18+'] * 0.7) + (temp['people aged <18'] * 0.5)
    people[year] = people[year].join(temp[['hhld_oecd_equ']])
    
    #
    people[year]['pc_income'] = people[year]['income anonymised'] / people[year][pop]
    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)
    people[year]['income_group'] = [x[0] for x in people[year]['income_group']] 
    
    # add variable on source of income
    people[year]['inc_source_code'] = 'Wages, benefits, pensions'
    people[year].loc[(people[year]['income_source'] == 3) | (people[year]['income_source'] == 6), 'inc_source_code'] = 'Other'  
        
    # gather spend      
    lcfs[year] = lcfs[year].loc[:,'1.1.1.1':'12.5.3.5'].astype(float).apply(lambda x: x*lcfs[year]['weight'])

# generate hhd emissions and multipliers only for regular years
hhd_ghg, multipliers = estimate_emissions.make_footprint({y:lcfs[y] for y in years}, wd)


##########
## SAVE ##
##########

# save multipliers
pickle.dump(multipliers, open(wd + 'data/processed/GHG_Estimates_LCFS/Multipliers_2007-2020.p','wb'))
 
# save emissions using their own year multipliers
for year in years:
    hhd_ghg[year] = people[year].join(hhd_ghg[year])
    hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year]['weight'])
    name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv'
    hhd_ghg[year].reset_index().to_csv(name)
    print(str(year) + ' saved')

# save emissions using ref_year multipliers
multiplier_ref_year = multipliers[ref_year][['multipliers']]
for year in [str(y) + '_cpi' for y in years]:
    temp = lcfs[year].T.join(multiplier_ref_year)
    temp = temp.apply(lambda x: x*temp['multipliers']).drop(['multipliers'], axis=1).T
    temp = people[year].join(temp)
    temp.loc[:,'1.1.1.1':'12.5.3.5'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/temp['weight'])
    hhd_ghg[year] = cp.copy(temp)
    name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '.csv'
    temp.to_csv(name)
    print(year +  ' with ' + str(ref_year) + ' multipliers saved')
    
# save emissions for 2020 using 2019 multipliers
ref_year = 2019; year = 2020
multiplier_ref_year = multipliers[ref_year][['multipliers']]

temp = lcfs[str(year) + '_' + str(ref_year) + 'cpi'].T.join(multiplier_ref_year)
temp = temp.apply(lambda x: x*temp['multipliers']).drop(['multipliers'], axis=1).T
temp = people[year].join(temp)
temp.loc[:,'1.1.1.1':'12.5.3.5'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/temp['weight'])
hhd_ghg[str(year) + '_' + str(ref_year) + 'cpi'] = cp.copy(temp)
name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '.csv'
temp.to_csv(name)
print(str(year) +  ' with ' + str(ref_year) + ' multipliers saved')