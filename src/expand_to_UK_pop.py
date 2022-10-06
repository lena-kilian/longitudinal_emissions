#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

calculating elasticities -- using 2007 mutipliers and expenditure adjusted to 2007 cpi

@author: lenakilian

Before this run:
    1. LCFS_import_data_function.py
    2. LCFS_import_data.py
    3. LCFS_estimate_emissions.py
    
Next run (various options): 
    - explore_plots.py
    - regression_data.py
    - 
"""

import pandas as pd
import pickle


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

ref_year = 2007 # choose year which expenditure is adjusted to (by CPI)

# product category lookup
cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'

# import data
hhd_ghg = {}
for year in list(range(2001, 2019)):
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv').set_index('case')
    hhd_ghg[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '_cpi.csv')
    
    
# reduce product categories to reduce data size
for year in list(hhd_ghg.keys()):
    hhd_ghg[year] = hhd_ghg[year].rename(columns=cat_dict).sum(axis=1, level=0)
    
# function to duplicate index
def reindex_df(df, weight_col):
    """expand the dataframe to prepare for resampling
    result is 1 row per count per sample"""
    df = df.reindex(df.index.repeat(df[weight_col]))
    df.reset_index(drop=True, inplace=True)
    return(df)

# expand data by number of households --> 'weight' variable
# reindex
hhd_ghg_uk = {}
for year in list(hhd_ghg.keys()):
    df = hhd_ghg[year].reset_index()[['case', 'weight', 'no people']]
    df['weight'] = df['weight'] * 10 # to get full population need to multiply by 1000 - doing 10 to get more accuracy  
    df['rep_weight'] = [int(round(x)) for x in df['weight']]
    # multiply index by rep_weight
    df = reindex_df(df[['case', 'rep_weight']], weight_col = 'rep_weight')

    hhd_ghg_uk[year] = df[['case']].merge(hhd_ghg[year].reset_index(), on=['case'])
    
pickle.dump(hhd_ghg_uk, open(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_population.p', 'wb'))