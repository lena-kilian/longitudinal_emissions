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
    - regression
"""

import pandas as pd
import estimate_emissions_main_function_2021 as estimate_emissions
import copy as cp
import pysal as ps


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

ref_year = 2007 # choose year which expenditure is adjusted to (by CPI)

hhd_type_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp3_lookup.xlsx', sheet_name='hhd_type')

years = list(range(2001, 2020))
pop = 'no people' # change this to oecd equivalised scale if needed

# load LFC data
lcfs = {}
people = {}


for year in years:
    # regular
    lcfs[year] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv').set_index('case')
    # with cpi
    temp = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '_wCPI_ref' + str(ref_year) + '.csv').set_index('case')
    lcfs[str(year) + '_cpi'] = lcfs[year].loc[:,:'1.1.1.1'].iloc[:,:-1].join(temp.loc[:,'1.1.1.1':'12.5.3.5'])

check = pd.DataFrame(index=[1])
for year in years:
    temp = lcfs[str(year) + '_cpi'][['7.3.4.1']]
    temp.columns = [str(year) + '_' + x for x in temp.columns]
    check = check.join(temp, how='outer')
for year in years:
    temp = lcfs[str(year) + '_cpi'][['7.3.4.2']]
    temp.columns = [str(year) + '_' + x for x in temp.columns]
    check = check.join(temp, how='outer')
    
check_sum = check.sum()


for year in list(lcfs.keys()):
    # separate sociodemographic variables
    people[year] = lcfs[year].loc[:,:'1.1.1.1'].iloc[:,:-1]
    
    # Classify household types
    relatives = ['child (adult)', 'child (minor)', 'grandchild (minor)', 'grandchild (adult)', 
                 'non-relative (minor)', 'non-relative (adult)', 'other relative (minor)', 'other relative (adult)', 'partner', 'sibling', 
                 'son/daughter-in-law', 'father/mother-in-law', 'people aged <18']
    temp = cp.copy(people[year][['parent/guardian'] + relatives])
    for item in relatives:
        temp.loc[temp[item] > 0, item] = True
        temp.loc[temp[item] == 0, item] = False
    temp = temp.merge(hhd_type_lookup, on=['parent/guardian'] + relatives)[['hhd_type']]
    
    people[year] = people[year].join(temp)
    
    # classify age range of hrp
    people[year]['age_group_hrp'] = 'Other'
    for i in [[18, 29], [30, 39], [40, 49], [50, 59], [60, 69], [70, 79]]:
        people[year].loc[people[year]['age hrp'] >= i[0], 'age_group_hrp'] = str(i[0]) + '-' + str(i[1])
    people[year].loc[people[year]['age hrp'] >= 80, 'age_group_hrp'] = '80 or older'
    
    # OECD household equivalent scales
    # https://www.oecd.org/economy/growth/OECD-Note-EquivalenceScales.pdf
    temp = cp.copy(people[year])
    temp['<16'] =  temp['people aged <18'] - temp['people aged 16-17']
    temp['16+'] = temp['no people'] - temp['<16']
    temp['hhld_oecd_mod'] = 0
    temp.loc[temp['16+'] > 0, 'hhld_oecd_mod'] = 1
    temp['hhld_oecd_equ'] = temp['hhld_oecd_mod']
    # OECD-modified scale
    temp['hhld_oecd_mod'] = temp['hhld_oecd_mod'] + ((temp['16+'] - 1) * 0.5) + (temp['<16'] * 0.3)
    people[year] = people[year].join(temp[['hhld_oecd_mod']])
    # OECD equivalence scale
    temp['hhld_oecd_equ'] = temp['hhld_oecd_equ'] + ((temp['16+'] - 1) * 0.7) + (temp['<16'] * 0.5)
    people[year] = people[year].join(temp[['hhld_oecd_equ']])
    
    #
    people[year]['pc_income'] = people[year]['income anonymised'] / people[year][pop]
    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)
    
    # gather spend      
    lcfs[year] = lcfs[year].loc[:,'1.1.1.1':'12.5.3.5'].astype(float).apply(lambda x: x*lcfs[year]['weight'])

# generate hhd emissions and multipliers only for regular years
hhd_ghg, multipliers = estimate_emissions.make_footprint({y:lcfs[y] for y in years}, wd)
 
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
    name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '.csv'
    temp.to_csv(name)
    print(year +  ' with 2007 multipliers saved')

    
