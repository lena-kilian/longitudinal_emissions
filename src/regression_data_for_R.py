#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 2022

Plots for specific comparisons

@author: lenakilian

Before this run:
    1. LCFS_import_data_function.py
    2. LCFS_import_data.py
    3. LCFS_estimate_emissions.py
    
Next run: elasticities_regression.R
"""
import pandas as pd
from sys import platform

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'

ref_year = 2007 # choose year which expenditure is adjusted to (by CPI)

# product category lookup
cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'


vars_ghg = [ 'Food and Drinks', 'Other consumption', 'Recreation, culture, and clothing', 'Housing, water and waste', 
            'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 'Air transport', 'Total']

vars_weighted_means = ['age hrp', 'pc_income',  'age_adults_mean', 'age_minors_mean', 'age_all_mean']

vars_hhd_level = ['no people', 'no_adults', 'no_females', 'no_males', 'people aged <18', 'rooms in accommodation']
    
    
# import data
hhd_ghg = pd.DataFrame(columns=['year'])
temp = {}
for year in list(range(2001, 2021)):
    temp[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv')
    temp[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '_cpi.csv')

# edit variables where needed
for year in list(temp.keys()):
    temp[year] = temp[year].rename(columns=cat_dict).sum(axis=1, level=0).set_index('case')
    
    temp[year]['Total'] = temp[year][vars_ghg[:-1]].sum(1)
    temp[year]['all'] = 'all_households'
    temp[year]['year'] = 'Year_' + str(year)[:4]
    if str(year)[-3:] == 'cpi':
        temp[year]['cpi'] = 'cpi'
    else:
        temp[year]['cpi'] = 'regular'
    
    hhd_ghg = hhd_ghg.append(temp[year].reset_index()[['case', 'year', 'cpi', 'age_group_hrp', 'income_group', 'all', 'income anonymised'] + vars_ghg])

income_dict = dict(zip(list(range(10)),
                       ['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest']))
hhd_ghg['income_group'] = hhd_ghg['income_group'].map(income_dict)

hhd_ghg.to_csv(wd + 'data/processed/GHG_Estimates_LCFS/Regression_data.csv')
    
    
