#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import estimate_emissions_main_function_2022 as estimate_emissions
import copy as cp


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

pop = 'no people'
years = [2019, 2020]

lcfs = {}
for year in years:
    lcfs[year] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '_wcpi.csv').set_index('case')

weight_2019 = lcfs[2019][[pop, 'weight']]
lcfs[2019] = lcfs[2019].loc[:,'1.1.1.1':'12.5.3.5'].astype(float).apply(lambda x: x*lcfs[2019]['weight'])

hhd_ghg, multipliers = estimate_emissions.make_footprint({x:lcfs[x] for x in [2019]}, wd)

# save emissions per capita using 2019 multipliers
lcfs[2019] = pd.DataFrame(lcfs[2019].sum(0)).rename(columns={0:'pc_exp'}).T
lcfs[2019] = lcfs[2019].apply(lambda x: x/(weight_2019['weight'] * weight_2019[pop]).sum())
temp2 = {}
for year in years:
    temp = lcfs[year].T.join(multipliers[2019][['multipliers']], how='right')
    temp = temp.apply(lambda x: x*temp['multipliers']).drop(['multipliers'], axis=1).T.reset_index()\
        .rename(columns={'index':'case'}).fillna(0).set_index('case').loc[:,'1.1.1.1':'12.5.3.5']
    name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2019_multipliers_' + str(year) + '_wCPI.csv'
    temp.to_csv(name)
    temp2[year] = temp
    print(str(year) + ' with 2019 multipliers saved')

    
