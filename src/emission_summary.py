#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 07 2022

Calculating summary statistics for longitudinal emissions

@author: lenakilian

Before this run:
    1. LCFS_import_data_function.py
    2. LCFS_import_data.py
    3. LCFS_estimate_emissions.py
    
Next run: eplore_plots.py
"""

import pandas as pd
import copy as cp


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
hhd_ghg = {}
for year in list(range(2001, 2020)):
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv')
    hhd_ghg[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '_cpi.csv')

# edit variables where needed
for year in list(hhd_ghg.keys()):
    hhd_ghg[year] = hhd_ghg[year].rename(columns=cat_dict).sum(axis=1, level=0).set_index('case')
    hhd_ghg[year]['pop'] = hhd_ghg[year]['weight'] * hhd_ghg[year]['no people']
    hhd_ghg[year]['no_females'] = hhd_ghg[year][['females aged <2', 'females aged 2-4', 'females aged 5-17', 'females aged 18-44', 'females aged 45-59',
                                                 'females aged 60-64', 'females aged 65-69', 'females aged >69']].sum(1)
    hhd_ghg[year]['no_males'] = hhd_ghg[year]['no people'] - hhd_ghg[year]['no_females']
    for item in ['age_adults_mean', 'age_minors_mean', 'age_all_mean']:
        hhd_ghg[year][item] = hhd_ghg[year][item] * hhd_ghg[year]['no people']
        
    hhd_ghg[year]['Total'] = hhd_ghg[year][vars_ghg[:-1]].sum(1)
    hhd_ghg[year]['all'] = 'all_households'

# calculate weighted means
results = pd.DataFrame(columns=['year'])
for item in ['hhd_type', 'age_group_hrp', 'income_group', 'gor modified', 'all']:
    temp_data = pd.DataFrame(columns=[item])
    for year in list(hhd_ghg.keys()):
        # generate temp df
        temp = cp.copy(hhd_ghg[year])
        temp = temp[vars_ghg + vars_weighted_means + vars_hhd_level + ['weight', 'pop']].apply(lambda x: pd.to_numeric(x, errors='coerce'))\
            .join(hhd_ghg[year][[item]])
        temp[item] = ['Group ' + str(x) for x in temp[item]]
        temp['year'] = str(year)
        temp_data = temp_data.append(temp) # save this to do all years combined
        # calculate weighted means
        # household level
        hhd_means = cp.copy(temp)[vars_hhd_level + ['weight', item]]
        hhd_means[vars_hhd_level] = hhd_means[vars_hhd_level].apply(lambda x: x * hhd_means['weight'])
        hhd_means = hhd_means.groupby(item).sum()
        hhd_means[vars_hhd_level] = hhd_means[vars_hhd_level].apply(lambda x: x / hhd_means['weight'])
        # person level
        mean = cp.copy(temp)
        mean.loc[:,:'age_all_mean'] = mean.loc[:,:'rooms in accommodation'].apply(lambda x: x * mean['weight'])
        mean = mean.groupby(item).sum()
        mean = mean.apply(lambda x: x / mean['pop'])[vars_ghg + vars_weighted_means].join(hhd_means)
        mean['group_var'] = item
        mean['year'] = int(str(year)[:4])
        if str(year)[-3:] == 'cpi':
            mean['cpi'] = 'with_cpi'
        else:
            mean['cpi'] = 'regular'
        # add count data
        count = cp.copy(temp)
        count['count'] = 1
        count = count.groupby(item).count()[['count']]
        # join count and mean
        temp = mean.join(count).reset_index().rename(columns={item:'group'})
        # append to results df
        results = results.append(temp)
    # get results for all years combined   
    temp_data['cpi'] = 'regular'
    temp_data.loc[temp_data['year'].str[-3:] == 'cpi', 'cpi'] = 'with_cpi'
    # repeat mean and count
    # calculate weighted means
    # household level
    hhd_means = cp.copy(temp_data)[vars_hhd_level + ['weight', item]]
    hhd_means[vars_hhd_level] = hhd_means[vars_hhd_level].apply(lambda x: x * hhd_means['weight'])
    hhd_means = hhd_means.groupby(item).sum()
    hhd_means[vars_hhd_level] = hhd_means[vars_hhd_level].apply(lambda x: x / hhd_means['weight'])
    # person level
    mean = cp.copy(temp_data)
    mean.loc[:,'Food and Drinks':'rooms in accommodation'] = mean.loc[:,'Food and Drinks':'rooms in accommodation'].apply(lambda x: x * mean['weight'])
    mean = mean.groupby([item, 'cpi']).sum()
    mean = mean.apply(lambda x: x / mean['pop'])[vars_ghg + vars_weighted_means].join(hhd_means)
    mean['group_var'] = item
    mean['year'] = 'all'
    # add count data
    count = cp.copy(temp_data)
    count['count'] = 1
    count = count.groupby([item, 'cpi']).count()[['count']]
    # join count and mean
    temp = mean.join(count).reset_index().rename(columns={item:'group'})
    # append to results df
    results = results.append(temp)

income_dict = dict(zip(['Group ' + str(x) for x in range(10)],
                       ['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest']))
results.loc[results['group_var'] == 'income_group', 'group'] = results.loc[results['group_var'] == 'income_group', 'group'].map(income_dict)

region_dict = dict(zip(['Group ' + str(x) for x in range(1, 13)],
                       ['North East', 'North West and Merseyside', 'Yorkshire and the Humber', 'East Midlands'	,
                       'West Midlands', 'Eastern', 'London', 'South East', 'South West', 'Wales', 'Scotland', 'Northern Ireland']))
results.loc[results['group_var'] == 'gor modified', 'group'] = results.loc[results['group_var'] == 'gor modified', 'group'].map(region_dict)

results['group'] = results['group'].str.replace('Group ', '')




results.to_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')