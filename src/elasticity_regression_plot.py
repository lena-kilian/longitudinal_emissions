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


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

results = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')
results['year_str'] = ['Year ' + str(x) for x in results['year']]

product_dict = {'Recreation, culture, and clothing':'Recreation,\nculture, and\nclothing',
                'Housing, water and waste':'Housing, water\nand waste',
                'Electricity, gas, liquid and solid fuels':'Electricity, gas,\nliquid and solid\nfuels',
                'Private and public road transport':'Private and public\nroad transport',
                'Food and Drinks':'Food and Drinks',
                'Other consumption':'Other\nconsumption',
                'Air transport':'Air transport',
                'Total':'Total'}

results_og = cp.copy(results)


"""
# shorten so code works
results = results.drop(['ci_low', 'ci_up'], axis=1)


all_results = pd.DataFrame(columns=['year'])
for item in ['income_group', 'composition of household', 'age_range']:
    fig, ax = plt.subplots(figsize=(7.5, 5))
    # Add household groups
    data = results.loc[(results['group_var'] == item) & (results['group'] != 'All households')].sort_values(['group', 'product', 'year'])
    if item == 'income_group':
        data['order'] = [int(x.replace('Decile ', '')) for x in data['group']]
        data = data.sort_values(['order', 'product', 'year'])
    if item == 'age_group':
        data = data.loc[(data['group'] != 'Household with children') & (data['group'] != 'Other')]
    data['product'] = data['year_str'] + ' ' + data['product']
    sns.scatterplot(ax=ax, data=data, x='product', y='elasticity', style='year_str', hue='group', s=70, 
                    palette='Blues', edgecolor='black', linewidth=0.2)
    
    all_results = all_results.append(data) # add data for category to all results
    
    # Add all households
    data = results.loc[(results['group_var'] == item) & (results['group'] == 'All households')].sort_values(['group', 'product', 'year'])
    data['product'] = data['year_str'] + ' ' + data['product']
    sns.set_palette(sns.color_palette(['#C54A43'])) # '#78AAC8'
    sns.scatterplot(ax=ax, data=data, x='product', y='elasticity', style='year_str', hue='group', s=100,
                    edgecolor='white', linewidth=1)
    # Add other details
    ax.axhline(0, linestyle='--', c='black', lw=0.5)
    for i in range(len(product_dict.keys())-1):
        ax.axvline(2*i+1.5, c='#c5c5c5', lw=0.5)
    ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
    # organise legend
    handles, labels = ax.get_legend_handles_labels()
    handles = [handles[0], handles[-4]] + handles[1:-8] + [handles[0], handles[0]] + handles [-2:]
    labels = ['Group'] + [labels[-4]] + labels[1:-8] + ['', 'Year'] + [x[-4:] for x in labels[-2:]]
    ax.legend(handles, labels, bbox_to_anchor=(1.3, 1))
    # x labels
    ax.tick_params(axis='x', labelrotation=90)
    temp = data[['product']].drop_duplicates()['product'].tolist()
    xlabs = []
    for i in range(0, len(temp), 2):
        xlabs.append('\n\n\n' + product_dict[temp[i][10:]])
        xlabs.append('')
    ax.set_xticklabels(xlabs)
    #ax.set_ylim(-1.5, 5)
    # save figure
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_' + item + '.png', bbox_inches='tight', dpi=200)
    plt.show()
    
    all_results = all_results.append(data) # add data for all households to all results
    
all_results['product'] = all_results['product'].str[10:]
all_results = all_results.set_index(['group_var', 'group', 'product', 'year_str']).drop('year', axis=1)\
    .unstack(level=['year_str', 'product'])['elasticity']
all_results = all_results[sorted(all_results.columns)]


# make plot with all households only
data = all_results.stack().stack().reset_index().rename(columns={0:'elasticity'})
data = data.loc[data['group'] == 'All households']
data['product_2'] = data['product'] + ' ' + data['year_str']
data = data.sort_values('product_2').drop('group_var', axis=1).drop_duplicates()
fig, ax = plt.subplots(figsize=(7.5, 5))
# Add household groups
sns.scatterplot(ax=ax, data=data, y='product_2', x='elasticity', hue='year_str', s=70, 
                palette='RdBu', edgecolor='black', linewidth=0.2)
# Add other details
ax.axhline(0, linestyle='--', c='black', lw=0.5)
for i in range(len(product_dict.keys())-1):
    ax.axvline(2*i+1.5, c='#c5c5c5', lw=0.5)
ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
# organise legend
ax.legend(bbox_to_anchor=(1, 0.65))
# x labels
ax.tick_params(axis='x', labelrotation=90)
temp = data[['product_2']].drop_duplicates()['product_2'].tolist()
xlabs = []
for i in range(0, len(temp), 2):
    xlabs.append('\n\n\n' + product_dict[temp[i][:-10]])
    xlabs.append('')
print(temp[i])
ax.set_xticklabels(xlabs)
#ax.set_ylim(-1.5, 5)
# save figure
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households.png', bbox_inches='tight', dpi=200)
plt.show()
"""

# make plot for all households with error bars
data = cp.copy(results_og)
data = data.loc[data['group'] == 'All households'].drop('group_var', axis=1).drop_duplicates()
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