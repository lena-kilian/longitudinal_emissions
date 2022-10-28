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


vars_ghg = ['Food and Drinks', 'Other consumption', 'Recreation, culture, and clothing', 'Housing, water and waste', 
            'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 'Air transport', 'Total']

vars_weighted_means = ['age hrp', 'income anonymised',  'age_adults_mean', 'age_minors_mean', 'age_all_mean']

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
hhd_ghg[2020] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2020.csv')
hhd_ghg['2020_cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_2020_cpi.csv')

group_dict = {'Average':'all_households', 
              'income_decile_1':'Lowest', 'income_decile_2':'2nd', 'income_decile_3':'3rd', 'income_decile_4':'4th', 'income_decile_5':'5th', 
              'income_decile_6':'6th', 'income_decile_7':'7th', 'income_decile_8':'8th', 'income_decile_9':'9th', 'income_decile_10':'Highest',
              'age_group_18_29':'18-29', 'age_group_30_49':'30-49', 'age_group_50_64':'50-64', 'age_group_65_74':'65-74', 'age_group_75':'75+'}
              # 40-49, 80+

for year in [2020, '2020_cpi']:
    hhd_ghg[year]['year'] = 2020
    if str(year)[-3:] == 'cpi':
        hhd_ghg[year]['cpi'] = 'with_cpi'
    else:
        hhd_ghg[year]['cpi'] = 'regular'
    hhd_ghg[year] = hhd_ghg[year].rename(columns=cat_dict).sum(axis=1, level=0)
    hhd_ghg[year] = hhd_ghg[year].rename(columns={'case':'group', 'COICOP4_code':'group_var'})
    hhd_ghg[year]['Total'] = hhd_ghg[year][vars_ghg[:-1]].sum(1)
    hhd_ghg[year]['group'] = hhd_ghg[year]['group'].map(group_dict)
    hhd_ghg[year]['group_var'] = hhd_ghg[year]['group_var'].map({'All':'all', 'Age of HRP':'age_group_hrp', 'Income decile':'income_group'})
    
    hhd_ghg[year][vars_ghg] = hhd_ghg[year][vars_ghg].apply(lambda x: x/hhd_ghg[year]['no people'])
    idx = results.columns.tolist()
    results = results.append(hhd_ghg[year])[idx]

results['pc_income'] = results['income anonymised'] / results['no people'] 
results['hhd_income_scaled'] = results['income anonymised'] / results['income anonymised'].max() * 100
results['pc_income_scaled'] = results['pc_income'] / results['pc_income'].max() * 100

results.to_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
