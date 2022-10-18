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
    4. emission_summary.py
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import copy as cp


axis = 'tCO$_{2}$e / capita'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':11})

ref_year = 2007

years = list(range(2001, 2020))

vars_ghg = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
            'Private and public road transport', 'Air transport', 
            'Recreation, culture, and clothing', 'Other consumption',
            'Total']

vars_ghg_dict = ['Food and\nDrinks', 'Housing, water\nand waste', 'Electricity, gas,\nliquid and\nsolid fuels', 
                 'Private and\npublic road\ntransport', 'Air transport', 
                 'Recreation,\nculture, and\nclothing', 'Other\nconsumption',
                 'Total']

group_dict = {'hhd_type':'Household Composition', 'age_group_hrp':'Age of HRP', 'gor modified':'Region', 
              'income_group':'Income Decile', 'all':'All'}

# import data
data_ghg = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
data_ghg = data_ghg.loc[(data_ghg['group'] != '0') & (data_ghg['group'] != 'Other')]
data_ghg['group'] = data_ghg['group']\
    .str.replace('Other relative household', 'Other relatives')\
        .str.replace('Single parent/guardian household', 'Single parent/\nguardian\nhousehold')\
            .str.replace('Two parent/guardian household', 'Two parent/guardian\nhousehold')\
                .str.replace(' with', '\nwith').str.replace('adult grand', 'adult\ngrand')

data_allyears = data_ghg.loc[data_ghg['year'] == 'all'] 
data_annual = data_ghg.loc[data_ghg['year'] != 'all'] 
data_annual['year'] = pd.to_datetime(data_annual['year'], format="%Y")

########################
# Lineplot comparisons #
########################

comparisons = [['Lowest', 'Highest'], ['all_households', '40-49'], ['Single occupant', 'Single parent/\nguardian\nhousehold'],
               ['Couple only', 'Two parent/guardian\nhousehold'], ['Single occupant', 'Multiple households'],
               #['North East', 'Wales', 'Scotland', 'Northern Ireland', 'North West and Merseyside', 'Yorkshire and the Humber', 
               # 'East Midlands', 'West Midlands', 'Eastern', 'London', 'South East', 'South West'],
               ['Northern Ireland', 'London'], ['Northern Ireland', 'Scotland', 'Wales'],
               #['Couple only', 'Multiple households', 'Other relatives', 'Single occupant', 'Single parent/\nguardian\nhousehold', 
               # 'Two parent/guardian\nhousehold']
               ['18-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
               #['18-29', '50-59', '60-69']
               ]

data = data_annual.set_index(['year', 'cpi', 'group'])[vars_ghg[:-1]].stack().reset_index().rename(columns={'level_3':'Product Category', 0:'ghg'})

data_ghg[['group_var']].drop_duplicates()

for comparison in comparisons:
    fig, axs = plt.subplots(nrows=len(vars_ghg[:-1]), ncols=2, sharex=True, sharey=True, figsize=(7.5, 10))
    for c in range(2):
        cpi = ['regular', 'with_cpi'][c]
        for r in range(len(vars_ghg[:-1])):
            item = vars_ghg[r]
            temp = data.loc[(data['group'].isin(comparison) == True) & (data['cpi'] == cpi) & (data['Product Category'] == item)]
            sns.lineplot(ax=axs[r, c], data=temp, x='year', y='ghg', hue='group')
            axs[0, c].set_title(['Own years', '2007 prices and multipliers'][c])
            axs[r, c].set_ylabel(vars_ghg_dict[r])
            plt.sca(axs[r, c])
            plt.xticks(rotation=90)
            plt.legend(bbox_to_anchor=(2, 1))
    plt.show()

########################
# Barchart comparisons #
########################