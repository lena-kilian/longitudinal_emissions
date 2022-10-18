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


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

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
for year in list(range(2001, 2020)):
    temp[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv')
    temp[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '_cpi.csv')

# edit variables where needed
for year in list(temp.keys()):
    temp[year] = temp[year].rename(columns=cat_dict).sum(axis=1, level=0).set_index('case')
    temp[year][vars_ghg[:-1]] = temp[year][vars_ghg[:-1]].apply(lambda x: x*temp[year]['no people'])
    
    temp[year]['Total'] = temp[year][vars_ghg[:-1]].sum(1)
    temp[year]['all'] = 'all_households'
    temp[year]['year'] = 'Year_' + str(year)[:4]
    if str(year)[-3:] == 'cpi':
        temp[year]['cpi'] = 'cpi'
    else:
        temp[year]['cpi'] = 'regular'
    
    hhd_ghg = hhd_ghg.append(temp[year].reset_index()[['case', 'year', 'cpi', 'hhd_type', 'age_group_hrp', 'income_group', 'gor modified', 'all', 'income anonymised'] + vars_ghg])

income_dict = dict(zip(list(range(10)),
                       ['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest']))
hhd_ghg['income_group'] = hhd_ghg['income_group'].map(income_dict)

region_dict = dict(zip(list(range(1, 13)),
                       ['North East', 'North West and Merseyside', 'Yorkshire and the Humber', 'East Midlands'	,
                       'West Midlands', 'Eastern', 'London', 'South East', 'South West', 'Wales', 'Scotland', 'Northern Ireland']))
hhd_ghg['gor modified'] = hhd_ghg['gor modified'].map(region_dict)

hhd_ghg.to_csv(wd + 'data/processed/GHG_Estimates_LCFS/Regression_data.csv')
    
    
