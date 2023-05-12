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
import matplotlib.pyplot as plt
from sys import platform
import matplotlib.patches as mpatches

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'

axis = 'tCO$_{2}$e'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':12})

vars_ghg = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
            'Private and public road transport', 'Air transport', 
            'Recreation, culture, and clothing', 'Other consumption',
            'Total']

vars_ghg_dict = ['Food and\nDrinks', 'Housing, water\nand waste', 'Electricity, gas,\nliquid and solid fuels', 
                 'Private and public\nroad transport', 'Air transport', 
                 'Recreation, culture,\nand clothing', 'Other\nconsumption',
                 'Total']

group_dict = {'hhd_type':'Household Composition', 'age_group_hrp':'Age of HRP', 'gor modified':'Region', 
              'income_group':'Income Decile', 'all':'All'}


# import data
data_ghg = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
data_ghg = data_ghg.loc[(data_ghg['group'] != '0') & (data_ghg['group'] != 'Other')]
data_ghg['group'] = data_ghg['group'].str.replace('all_households', 'All households')

data_comp = data_ghg.loc[(data_ghg['year'].isin(['2007', '2009', '2019', '2020']) == True) & (data_ghg['pc'] == 'hhld_oecd_mod')]
data_comp['type'] = data_comp['year'].map({'2007':'2007-2009', '2009':'2007-2009', '2019':'2019-2020', '2020':'2019-2020'})
data_comp['year_type'] = data_comp['year'].map({'2007':'First year', '2009':'Last year', '2019':'First year', '2020':'Last year'})

data_comp['keep'] = False
data_comp.loc[(data_comp['year'] == '2007') & (data_comp['cpi'] == 'regular'), 'keep'] = True
data_comp.loc[(data_comp['year'] == '2009') & (data_comp['cpi'] == 'with_cpi'), 'keep'] = True
data_comp.loc[(data_comp['year'] == '2019') & (data_comp['cpi'] == 'regular'), 'keep'] = True
data_comp.loc[(data_comp['year'] == '2020') & (data_comp['cpi'] == 'with_cpi19'), 'keep'] = True

data_comp = data_comp.loc[data_comp['keep'] == True].drop(['keep', 'cpi', 'pc'], axis=1)

data_comp = data_comp.set_index(['type', 'year_type', 'group', 'group_var'])[vars_ghg + ['pc_income']].unstack(level=['type', 'year_type'])\
    .swaplevel(axis=1).swaplevel(axis=1, i=0, j=1).swaplevel(axis=1, i=2, j=1)

for event in ['2007-2009', '2019-2020']:
    for product in vars_ghg + ['pc_income']:
        data_comp[('Difference', event, product)] = data_comp[('Last year', event, product)] - data_comp[('First year', event, product)]
        data_comp[('Percentage difference', event, product)] = data_comp[('Difference', event, product)] / data_comp[('First year', event, product)] * 100
        
data_comp = data_comp.stack().stack().reset_index()

order = ['All households', '18-29', '30-49', '50-64', '65-74', '75+', 'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest']
data_comp['group_cat'] = data_comp['group'].astype('category').cat.set_categories(order, ordered=True)

data_comp = data_comp.sort_values('group_cat')

check = data_comp.set_index(['group', 'group_var', 'level_2', 'type', 'group_cat']).unstack(level='level_2').stack(level=0)[
    ['pc_income', 'Total', 'Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 
     'Air transport', 'Recreation, culture, and clothing', 'Other consumption']].reset_index().sort_values(['year_type', 'type', 'group_cat'])


##########
## PLOT ##
##########

prods = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 
         'Air transport', 'Recreation, culture, and clothing', 'Other consumption']


supergroups = ['All', 'Age', 'Income']
supergroups_dicts = {'All':['All households'], 'Age':['18-29', '30-49', '50-64', '65-74', '75+'], 'Income':['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest']}

results_filtered = check.loc[(check['year_type'] != 'Percentage difference') & (check['year_type'] != 'Difference')]

color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']

max_co2 = results_filtered['Total'].max() * 1.05
max_inc = results_filtered['pc_income'].max() * 1.05

for years in ['2007-2009', '2019-2020']:
    temp = results_filtered.loc[results_filtered['type'] == years]
    temp['Year'] = temp['year_type'].map({'First year':years[:4], 'Last year':years[-4:]})
    
    for item in supergroups:
        groups = supergroups_dicts[item]
        
        fig, ax = plt.subplots(ncols=len(groups), figsize=(1.1*len(groups), 5), sharey=True)
            
        for i in range(len(groups)):
            group = groups[i]
            temp2 = temp.loc[temp['group_cat'] == group]
            temp2 = temp2.set_index('Year')[prods + ['pc_income']]
            
            # axis left
            if item == 'All':
                ax1 = ax
            else:
                ax1 = ax[i]                
            start = [0, 0]
            patch_list = []
            for j in range(len(prods)):
                prod = prods[j]
                height = temp2[prod]
                ax1.bar(bottom=start, height=height, x=temp2.index, edgecolor='k', linewidth=0.5, color=color_list[j])
                start += height
                patch_list.append(mpatches.Patch(color=color_list[j], label=prod))
            ax1.set_xlabel(group)
            ax1.set_ylim(0, max_co2)
            if i == 0:
                ax1.set_ylabel(axis)
            if item == 'All':
                patch_list.reverse()
                plt.legend(handles=patch_list, bbox_to_anchor=(-1, 1))

            # axis right
            ax2 = ax1.twinx()
            ax2.scatter(temp2.index, temp2['pc_income'], color='k')
            ax2.set_ylim(0, max_inc)
            if i != len(groups)-1:
                ax2.set(yticklabels=[])
            else:
                ax2.set_ylabel('Income (weekly)')
            if item == 'All':
                plt.legend(['Income'], bbox_to_anchor=(-1, 0))
            # modify plot

        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_compare_' + years + '_' + item + '.png',
                    bbox_inches='tight', dpi=300)
        plt.show() 
        
        
results = data_comp.set_index(['group_cat', 'group_var', 'level_2', 'type'])[['Percentage difference']].unstack(level=['type', 'level_2'])
