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


vars_ghg = ['Food and Drinks', 'Other consumption', 'Recreation, culture, and clothing', 'Housing, water and waste', 
            'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 'Air transport', 'Total']

vars_weighted_means = ['age hrp', 'income anonymised',  'age_adults_mean', 'age_minors_mean', 'age_all_mean']

vars_hhd_level = ['no people', 'no_adults', 'no_females', 'no_males', 'people aged <18', 'rooms in accommodation', 'hhld_oecd_equ', 'hhld_oecd_mod']
    
    
# import data
hhd_ghg = {}
for year in list(range(2001, 2021)):
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv')
    hhd_ghg[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '_cpi.csv')
hhd_ghg['2020_2019cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(2019) + '_multipliers_' + str(2020) + '_cpi.csv')

# edit variables where needed
for year in list(hhd_ghg.keys()):
    hhd_ghg[year] = hhd_ghg[year].rename(columns=cat_dict).sum(axis=1, level=0).set_index('case')
    hhd_ghg[year]['pop'] = hhd_ghg[year]['weight'] * hhd_ghg[year]['no people']
    hhd_ghg[year]['no_females'] = hhd_ghg[year][['females aged <2', 'females aged 2-4', 'females aged 5-17', 'females aged 18-44', 'females aged 45-59',
                                                 'females aged 60-64', 'females aged 65-69', 'females aged >69']].sum(1)
    hhd_ghg[year]['no_males'] = hhd_ghg[year]['no people'] - hhd_ghg[year]['no_females']        
    hhd_ghg[year]['Total'] = hhd_ghg[year][vars_ghg[:-1]].sum(1)
    hhd_ghg[year]['all'] = 'all_households'

# calculate weighted means
results = pd.DataFrame(columns=['year'])
for item in ['age_group_hrp', 'income_group', 'all']: #'hhd_type','gor modified', 
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
        
        # person level
        mean = temp[vars_ghg + ['weight', 'pop', item]]
        mean[vars_ghg] = mean[vars_ghg].apply(lambda x: x * mean['weight'])
        mean = mean.groupby(item).sum()
        mean[vars_ghg] = mean[vars_ghg].apply(lambda x: x / mean['pop'])
        
        # treat weighted means for soc-dem differently
        mean_w = temp[vars_weighted_means + ['weight', 'no people', 'no_adults', item]]
        mean_w['pop_minors'] = mean_w['weight'] * (mean_w['no people'] - mean_w['no_adults'])
        mean_w['pop_adults'] = mean_w['weight'] * mean_w['no_adults']
        mean_w['pop_all'] = mean_w['weight'] * mean_w['no people']
        # age minors needs to be multiplied by number of minors
        mean_w['age_minors_mean'] = mean_w['age_minors_mean'] * (mean_w['no people'] - mean_w['no_adults'])
        # age adults needs to be multiplied by number of adults
        mean_w['age_adults_mean'] = mean_w['age_adults_mean'] * mean_w['no_adults']
        # age all needs to be multiplied by number of people
        mean_w['age_all_mean'] = mean_w['age_all_mean'] * mean_w['no people']
        mean_w[vars_weighted_means] = mean_w[vars_weighted_means].apply(lambda x: x * mean_w['weight'])
        mean_w = mean_w.groupby(item).sum()
        # income and age of hrp only need to be divided by weight, do this at end
        mean_w[['age hrp', 'income anonymised']] = mean_w[['age hrp', 'income anonymised']].apply(lambda x: x/mean_w['weight'])
        # age groups needs to be divided by age pop
        for a in ['all', 'adults', 'minors']:
            mean_w['age_' + a + '_mean'] = mean_w['age_' + a + '_mean'] / mean_w['pop_' + a] 
            
        # combine dfs        
        mean = mean[vars_ghg].join(mean_w[vars_weighted_means]).join(hhd_means)
        mean['group_var'] = item
        mean['year'] = int(str(year)[:4])
        if str(year)[-4:] == '_cpi':
            mean['cpi'] = 'with_cpi'
        elif str(year)[-4:] == '9cpi':
            mean['cpi'] = 'with_cpi19'
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
    temp_data.loc[temp_data['year'].str[-4:] == '_cpi', 'cpi'] = 'with_cpi'
    temp_data.loc[temp_data['year'].str[-4:] == '9cpi', 'cpi'] = 'with_cpi19'
    # repeat mean and count
    # calculate weighted means
    # household level
    hhd_means = cp.copy(temp_data)[vars_hhd_level + ['weight', item, 'cpi']]
    hhd_means[vars_hhd_level] = hhd_means[vars_hhd_level].apply(lambda x: x * hhd_means['weight'])
    hhd_means = hhd_means.groupby([item, 'cpi']).sum()
    hhd_means[vars_hhd_level] = hhd_means[vars_hhd_level].apply(lambda x: x / hhd_means['weight'])

    # person level
    mean = temp_data[vars_ghg + ['weight', 'pop', item, 'cpi']]
    mean[vars_ghg] = mean[vars_ghg].apply(lambda x: x * mean['weight'])
    mean = mean.groupby([item, 'cpi']).sum()
    mean[vars_ghg] = mean[vars_ghg].apply(lambda x: x / mean['pop'])
    
    # treat weighted means for soc-dem differently
    mean_w = temp_data[vars_weighted_means + ['weight', 'no people', 'no_adults', item, 'cpi']]
    mean_w['pop_minors'] = mean_w['weight'] * (mean_w['no people'] - mean_w['no_adults'])
    mean_w['pop_adults'] = mean_w['weight'] * mean_w['no_adults']
    mean_w['pop_all'] = mean_w['weight'] * mean_w['no people']
    # age minors needs to be multiplied by number of minors
    mean_w['age_minors_mean'] = mean_w['age_minors_mean'] * (mean_w['no people'] - mean_w['no_adults'])
    # age adults needs to be multiplied by number of adults
    mean_w['age_adults_mean'] = mean_w['age_adults_mean'] * mean_w['no_adults']
    # age all needs to be multiplied by number of people
    mean_w['age_all_mean'] = mean_w['age_all_mean'] * mean_w['no people']
    mean_w[vars_weighted_means] = mean_w[vars_weighted_means].apply(lambda x: x * mean_w['weight'])
    mean_w = mean_w.groupby([item, 'cpi']).sum()
    # income and age of hrp only need to be divided by weight, do this at end
    mean_w[['age hrp', 'income anonymised']] = mean_w[['age hrp', 'income anonymised']].apply(lambda x: x/mean_w['weight'])
    # age groups needs to be divided by age pop
    for a in ['all', 'adults', 'minors']:
        mean_w['age_' + a + '_mean'] = mean_w['age_' + a + '_mean'] / mean_w['pop_' + a] 
    
    # combine dfs        
    mean = mean[vars_ghg].join(mean_w[vars_weighted_means]).join(hhd_means)
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

# add 2020 data

# add equivalised results
results[vars_ghg] = results[vars_ghg].apply(lambda x: x*results['no people'])

results['pc'] = 'no people'
# add old equ
temp = cp.copy(results)
temp2 = cp.copy(results)
temp['no people'] = temp['hhld_oecd_equ']
temp['pc'] = 'hhld_oecd_equ'
results = results.append(temp)
# add mod equ
temp2['no people'] = temp2['hhld_oecd_mod']
temp2['pc'] = 'hhld_oecd_mod'
results = results.append(temp2)

results['pc_income'] = results['income anonymised'] / results['no people'] 
results[vars_ghg] = results[vars_ghg].apply(lambda x: x/results['no people'])

results = results.drop(['hhld_oecd_equ', 'hhld_oecd_mod'], axis=1)

results['group'] = results['group'].str.replace('all_households', 'All households')

results.to_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')

order = ['All households', 'Other', '18-29', '30-49', '50-64', '65-74', '75+', 'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest']
results['group_cat'] = results['group'].astype('category').cat.set_categories(order, ordered=True)
results = results.sort_values(['year', 'pc', 'cpi', 'group_cat'])