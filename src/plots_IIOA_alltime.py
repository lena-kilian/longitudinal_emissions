#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 2022

Plots for all years (2001-2019)

@author: lenakilian

Before this run:
    1. LCFS_import_data_function.py
    2. LCFS_import_data.py
    3. LCFS_estimate_emissions.py
    4. emission_summary.py
"""

import pandas as pd
import copy as cp
from sys import platform
import matplotlib.pyplot as plt
from statsmodels.stats.weightstats import DescrStatsW
import seaborn as sns
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
from bioinfokit.analys import stat
import statsmodels.api as sm
from statsmodels.formula.api import ols

res = stat()

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'
    
axis = 'tCO$_{2}$e/SPH'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':12})

ref_year = 2015

years = list(range(2001, 2021))

group_dict = dict(zip(['All', '18-29', '30-49', '50-64', '65-74', '75+', 
                       0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ,'Other'], 
                      ['All housheolds', 'Age 18-29', 'Age 30-49', 'Age 50-64', 'Age 65-74', 'Age 75+',
                       'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest', 'Other']))

# import lookups
col = 'Category_3'
cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup[col]))
cat_dict['pc_income'] = 'pc_income'

vars_ghg = cat_lookup[[col]].drop_duplicates()[col].tolist() + ['Total']

# import data and clean
hhd_ghg = {}; pc_ghg = {}
for year in years:
    #hhd_ghg[str(year)] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv')
    hhd_ghg[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(ref_year) + '_multipliers_' + str(year) + '_cpi.csv')

years = list(hhd_ghg.keys())
for year in years:
    hhd_ghg[year] = hhd_ghg[year].rename(columns=cat_dict).sum(axis=1, level=0)
    hhd_ghg[year]['Total'] = hhd_ghg[year][vars_ghg[:-1]].sum(1)
    hhd_ghg[year] = hhd_ghg[year].loc[hhd_ghg[year]['age_group_hrp'] != 'Other']
    
    pc_ghg[year] = cp.copy(hhd_ghg[year])
    pc_ghg[year][['income anonymised'] + vars_ghg] = pc_ghg[year][['income anonymised'] + vars_ghg].apply(lambda x: x/pc_ghg[year]['hhld_oecd_mod'])
    pc_ghg[year]['pop_mod'] = pc_ghg[year]['hhld_oecd_mod'] * pc_ghg[year]['weight']
    
    
# weighted se and mean
summary = pd.DataFrame(columns=['year'])
for cat in vars_ghg + ['income anonymised']:
    for year in years:
        # All households
        temp = pd.DataFrame(index=[0]);
        temp['year'] = year; temp['product'] = cat; temp['hhd_group'] = 'All'; temp['group'] = group_dict['All'];
        
        weighted_stats = DescrStatsW(pc_ghg[year][cat], weights=pc_ghg[year]['pop_mod'], ddof=0);
        temp['mean'] = weighted_stats.mean; temp['se'] = weighted_stats.std_mean;
        
        summary = summary.append(temp);
        
        # Age and income groups
        for item in ['age_group_hrp', 'income_group']:
            for group in pc_ghg[year][[item]].drop_duplicates()[item]:
                temp_data = pc_ghg[year].loc[pc_ghg[year][item] == group];
                
                temp = pd.DataFrame(index=[0]);
                temp['year'] = year; temp['product'] = cat; temp['hhd_group'] = item; temp['group'] = group_dict[group];
                
                weighted_stats = DescrStatsW(temp_data[cat], weights=temp_data['pop_mod'], ddof=0);
                temp['mean'] = weighted_stats.mean; temp['se'] = weighted_stats.std_mean;
                
                summary = summary.append(temp);
        print(year)
    print(cat)

summary['year'] = [int(x[:4]) for x in summary['year']]

order = ['Food and non-alcoholic drinks', 'Eating and drinking out',
         'Private transport', 'Public transport', 'Air transport',
         'Clothing and footwear', 'Recreation and culture', 'Accommodation services and package holidays',
         'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 'Furnishing and home maintenance',
         'Healthcare', 'Other goods and services']

cmap = matplotlib.cm.get_cmap('tab20c')
cmap = [matplotlib.colors.rgb2hex(cmap(x)) for x in range(cmap.N)]

for item in summary[['group']].drop_duplicates()['group']:
    plot_data = summary.loc[summary['group'] == item].set_index(['year', 'product'])[['mean', 'se']]
    plot_data = check4.set_index('group')[comp][order]
    plot_data.plot(kind='bar', stacked=True, figsize=(7.5, 5), cmap=my_cmap)
    plt.xlabel('Household Group'); plt.ylabel('Change in ' + axis)
    plt.title(comp)
    plt.axhline(0, c='k', linestyle=':')
    plt.axvline(0.5, c='k'); plt.axvline(5.5, c='k')
    plt.legend(bbox_to_anchor = (1,1))
    plt.show()
