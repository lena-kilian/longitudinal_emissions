#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import copy as cp
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import LCFS_import_data_function as lcfs_import
import pysal as ps
import numpy as np


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

results = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')
results['year_str'] = ['Year ' + str(x) for x in results['year']]
results = results.loc[results['cpi'] == 'regular']

product_dict = {'Recreation, culture, and clothing':'Recreation,\nculture, and\nclothing',
                'Housing, water and waste':'Housing, water\nand waste',
                'Electricity, gas, liquid and solid fuels':'Electricity, gas,\nliquid and solid\nfuels',
                'Private and public road transport':'Private and public\nroad transport',
                'Food and Drinks':'Food and Drinks',
                'Other consumption':'Other\nconsumption',
                'Air transport':'Air transport',
                'Total':'Total'}

results = results.loc[(results['group'].isin(['All households', 'Other', 'Household with children', '0']) == False)].dropna(how='any')

results['group_cat'] = results['group'].astype('category').cat.reorder_categories(
    ['all_households', 
     '18-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+',
     'Single occupant', 'Couple only',  'Single parent/guardian household', 'Two parent/guardian household', 'Other relative household', 'Multiple households',
     'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest', 
     'North East', 'North West and Merseyside', 'Yorkshire and the Humber', 'East Midlands', 'West Midlands', 'Eastern', 'London', 'South East',
     'South West', 'Wales', 'Scotland', 'Northern Ireland'])

results_og = cp.copy(results.sort_values(['product', 'group']))


# make plot for all households with error bars
data = cp.copy(results_og)
data = data.loc[data['group'] == 'all_households'].drop('group_var', axis=1).drop_duplicates()
data['product_2'] = data['product'] + ' ' + data['year_str']
data = data.sort_values('product_2')
data['ci_low'] = data['elasticity'] - data['ci_low']
data['ci_up'] = data['ci_up'] - data['elasticity']

fig, ax = plt.subplots(figsize=(7.5, 5))
# Add household groups
plt.errorbar(x=data['elasticity'], y=data['product_2'],
             xerr=np.array([data['ci_low'], data['ci_up']]),
             capsize=3, ls='none', color='k', linewidth=0.5)
sns.scatterplot(ax=ax, data=data, y='product_2', x='elasticity', hue='year_str', s=70, 
                palette='RdBu', edgecolor='black', linewidth=0.2)
# Add other details
ax.axvline(0, linestyle='--', c='black', lw=0.5)
for i in range(len(product_dict.keys())-1):
    ax.axhline(2*i+1.5, c='#c5c5c5', lw=0.5)
ax.set_xlabel('Income elasticities'); ax.set_ylabel('')
# organise legend
ax.legend(bbox_to_anchor=(1, 0.65))
# x labels
#ax.tick_params(axis='x', labelrotation=90)
temp = data[['product_2']].drop_duplicates()['product_2'].tolist()
ylabs = []
for i in range(0, len(temp), 2):
    ylabs.append('\n' + temp[i][:-10])
    ylabs.append('')
print(temp[i])
ax.set_yticklabels(ylabs)
#ax.set_ylim(-1.5, 5)
# save figure
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_T.png', bbox_inches='tight', dpi=200)
plt.show()


# make plot by type with error bars
all_data = results_og.loc[(results_og['group'].isin(['All households', 'Other', 'Household with children', '0']) == False)].dropna(how='any')
for item in all_data[['group_var']].drop_duplicates()['group_var']:
    data = all_data.loc[all_data['group_var'] == item].drop('group_var', axis=1)
    data['product_2'] = data['product'] #+ ' ' + data['year_str']
    data['ci_low'] = data['elasticity'] - data['ci_low']
    data['ci_up'] = data['ci_up'] - data['elasticity']

    fig, ax = plt.subplots(figsize=(7.5, 5))
    # Add household groups
    #plt.errorbar(x=data['elasticity'], y=data['product_2'],
    #             xerr=np.array([data['ci_low'], data['ci_up']]),
    #             capsize=3, ls='none', color='k', linewidth=0.5)
    sns.scatterplot(ax=ax, data=data, y='product_2', x='elasticity', hue='group', s=70, # hue='year_str',
                    palette='RdBu', edgecolor='black', linewidth=0.2)
    # Add other details
    ax.axvline(0, linestyle='--', c='black', lw=0.5)
    plt.legend(bbox_to_anchor=(1, 0.65))
    """
    for i in range(len(product_dict.keys())-1):
        ax.axhline(2*i+1.5, c='#c5c5c5', lw=0.5)
    ax.set_xlabel('Income elasticities'); ax.set_ylabel('')
    # organise legend
    ax.legend(bbox_to_anchor=(1, 0.65))
    # x labels
    #ax.tick_params(axis='x', labelrotation=90)
    temp = data[['product_2']].drop_duplicates()['product_2'].tolist()
    ylabs = []
    for i in range(0, len(temp), 2):
        ylabs.append('\n' + temp[i][:-10])
        ylabs.append('')
    print(temp[i])
    ax.set_yticklabels(ylabs)
    """
    #ax.set_ylim(-1.5, 5)
    # save figure
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_' + item + '.png', bbox_inches='tight', dpi=200)
    plt.show()