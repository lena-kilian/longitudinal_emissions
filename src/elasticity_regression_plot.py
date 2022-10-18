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

years = list(range(2001, 2020))

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

results_og = results.loc[results['year'] != 'all'].sort_values(['product', 'group'])
results_og['year'] = results_og['year'].astype(int)
results_og = results_og.loc[results_og['year'].isin(years) == True]
results_all_years = results.loc[results['year'] == 'all'].sort_values(['product', 'group'])


# make plot for all households with error bars
data = cp.copy(results_all_years)
data = data.loc[data['group'] == 'all_households'].drop('group_var', axis=1).drop_duplicates()
data['ci_low'] = data['elasticity'] - data['ci_low']
data['ci_up'] = data['ci_up'] - data['elasticity']

fig, ax = plt.subplots(figsize=(7.5, 5))
# Add household groups
plt.errorbar(x=data['elasticity'], y=data['product'],
             xerr=np.array([data['ci_low'], data['ci_up']]),
             capsize=3, ls='none', color='k', linewidth=0.5)
sns.scatterplot(ax=ax, data=data, y='product', x='elasticity', s=70, 
                palette='RdBu', edgecolor='black', linewidth=0.2)
# Add other details
ax.axvline(0, linestyle='--', c='black', lw=0.5)
ax.set_xlabel('Income elasticities'); ax.set_ylabel('')
plt.title('all years all households combined')
# save figure
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_T_allyears.png', bbox_inches='tight', dpi=200)
plt.show()

# make lineplots

for group in ['all_households']: #results_og[['group']].drop_duplicates()['group'].tolist():
    data = results_og.loc[results_og['group'] == group].sort_values(['product', 'group_cat'])
    group_var = data['group_var'].tolist()[0]
    # make lineplot
    fig, ax = plt.subplots(figsize=(7.5, 5))
    # Add household groups
    sns.lineplot(ax=ax, data=data, y='elasticity', x='year', hue='product', palette='colorblind')
    ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
    # organise legend
    ax.legend(bbox_to_anchor=(1, 0.65))
    plt.title(group_var + ': ' + group)
    # save figure
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_' + group_var + '_' + group.replace('/', '_') + '_lineplot.png', bbox_inches='tight', dpi=200)
    plt.show()


# make plot for all households with error bars flipped hue and y - flipped
maxmin = results_og.describe()['elasticity']
for group in results_og[['group_var']].drop_duplicates()['group_var'].tolist():
    data = cp.copy(results_og)
    data = data.loc[data['group_var'] == group].drop('group_var', axis=1).drop_duplicates()
    data['ci_low'] = data['elasticity'] - data['ci_low']
    data['ci_up'] = data['ci_up'] - data['elasticity']
    data = data.sort_values(['product', 'group_cat'])
    
    temp = cp.copy(data)
    fig, ax = plt.subplots(figsize=(len(data[['group']].drop_duplicates()), 5))
    # Add household groups
    sns.boxplot(ax=ax, data=temp, x='group', y='elasticity', hue='product',
                palette='colorblind', linewidth=0.75) #notch=True, 
    # Add other details
    ax.axhline(0, linestyle='--', c='black', lw=0.5)
    for i in range(len(data[['group']].drop_duplicates())):
        ax.axvline(i+0.5, linestyle='--', c='black', lw=0.5)
    ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
    # organise legend
    plt.ylim(maxmin['min']*0.95, maxmin['max']*1.05)
    plt.xticks(rotation=90)
    plt.legend(bbox_to_anchor=(1.3, 0.65))
    # save figure
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_styleBox_' + group + '.png', bbox_inches='tight', dpi=200)
    plt.show()
    
# make plot for all households with error bars flipped hue and y - flipped
maxmin = results_og.describe()['elasticity']
for group in results_og[['group_var']].drop_duplicates()['group_var'].tolist():
    data = cp.copy(results_og)
    data = data.loc[data['group_var'] == group].drop('group_var', axis=1).drop_duplicates()
    data['year_str'] = data['year'].astype(str)
    
    temp = cp.copy(data)
    fig, ax = plt.subplots(figsize=(len(data[['year']].drop_duplicates()), 5))
    # Add household groups
    sns.boxplot(ax=ax, data=temp, x='year_str', y='elasticity', hue='product',
                palette='colorblind', linewidth=0.75, showfliers = False) #notch=True, 
    # Add other details
    ax.axhline(0, linestyle='--', c='black', lw=0.5)
    for i in range(len(data[['year']].drop_duplicates())):
        ax.axvline(i+0.5, linestyle='--', c='black', lw=0.5)
    ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
    # organise legend
    plt.ylim(maxmin['min']*0.95, maxmin['max']*1.05)
    plt.xticks(rotation=90)
    plt.legend(bbox_to_anchor=(1.3, 0.65))
    # save figure
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_styleBox_all_years' + group + '.png', bbox_inches='tight', dpi=200)
    plt.show()
    
    
data = cp.copy(results_all_years)
temp = cp.copy(data)
fig, ax = plt.subplots(figsize=(len(data[['product']].drop_duplicates())*1.5, 5))
# Add household groups
sns.boxplot(ax=ax, data=temp, x='product', y='elasticity', hue='group_var',
            palette='colorblind', linewidth=0.75, showfliers = False) #notch=True, 
# Add other details
ax.axhline(0, linestyle='--', c='black', lw=0.5)
for i in range(len(data[['product']].drop_duplicates())):
    ax.axvline(i+0.5, linestyle='--', c='black', lw=0.5)
ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
# organise legend
plt.xticks(rotation=90)
plt.legend(bbox_to_anchor=(1.3, 0.65))
# save figure
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_styleBox_all_years_all.png', bbox_inches='tight', dpi=200)
plt.show()



years = [2007, 2009]

# make plot for all households with error bars
data = cp.copy(results_og)
data = data.loc[data['year'].isin(years) == True]
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
    

# make plot for all households with error bars
for group in results_og[['group_var']].drop_duplicates()['group_var'].tolist():
    data = cp.copy(results_og)
    data = data.loc[data['group_var'] == group].drop('group_var', axis=1).drop_duplicates()
    data['product_2'] = data['product'] + ' ' + data['group']
    data = data.sort_values('product_2')
    data['ci_low'] = data['elasticity'] - data['ci_low']
    data['ci_up'] = data['ci_up'] - data['elasticity']
    
    for year in years:
        temp = data.loc[data['year'] == year]
        fig, ax = plt.subplots(figsize=(5, len(data[['group']].drop_duplicates())))
        # Add household groups
        plt.errorbar(x=temp['elasticity'], y=temp['product_2'],
                     xerr=np.array([temp['ci_low'], temp['ci_up']]),
                     capsize=0, ls='none', color='k', linewidth=0.5)
        sns.scatterplot(ax=ax, data=temp, y='product_2', x='elasticity', hue='group', s=60, 
                        palette='RdBu', edgecolor='black', linewidth=0.2)
        # Add other details
        ax.axvline(0, linestyle='--', c='black', lw=0.5)
        ax.set_xlabel('Income elasticities'); ax.set_ylabel('')
        # organise legend
        ax.legend(bbox_to_anchor=(1, 0.65))
        # x labels
        #ax.tick_params(axis='x', labelrotation=90)
        temp2 = temp[['product']].drop_duplicates()['product'].tolist()
        ylabs = []
        for i in range(len(temp2)):
            k = int(((len(data[['group']].drop_duplicates())-1)/2)-0.5)
            if i>0:
                ax.axhline(i*len(data[['group']].drop_duplicates())-0.5, c='#c5c5c5', lw=0.5)
            name = ''
            for j in range(k):
                name += '\n'
            ylabs.append(name + temp2[i])
            for j in range(len(data[['group']].drop_duplicates())-1):
                ylabs.append('')
        ax.set_yticklabels(ylabs)
        plt.legend(bbox_to_anchor=(1.3, 0.65))
        #ax.set_ylim(-1.5, 5)
        # save figure
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_T_' + group + '_' + str(year) + '.png', bbox_inches='tight', dpi=200)
        plt.show()



# make plot for all households with error bars flipped hue and y
for group in results_og[['group_var']].drop_duplicates()['group_var'].tolist():
    data = cp.copy(results_og)
    data = data.loc[data['group_var'] == group].drop('group_var', axis=1).drop_duplicates()
    data['product_2'] = data['group'] + data['product']
    data = data.sort_values('product_2')
    data['ci_low'] = data['elasticity'] - data['ci_low']
    data['ci_up'] = data['ci_up'] - data['elasticity']
    
    for year in years:
        temp = data.loc[data['year'] == year]
        fig, ax = plt.subplots(figsize=(5, len(data[['group']].drop_duplicates())))
        # Add household groups
        plt.errorbar(x=temp['elasticity'], y=temp['product_2'],
                     xerr=np.array([temp['ci_low'], temp['ci_up']]),
                     capsize=0, ls='none', color='k', linewidth=0.5)
        sns.scatterplot(ax=ax, data=temp, y='product_2', x='elasticity', hue='product', s=60, 
                        palette='RdBu', edgecolor='black', linewidth=0.2)
        # Add other details
        ax.axvline(0, linestyle='--', c='black', lw=0.5)
        ax.set_xlabel('Income elasticities'); ax.set_ylabel('')
        # organise legend
        ax.legend(bbox_to_anchor=(1, 0.65))
        # x labels
        #ax.tick_params(axis='x', labelrotation=90)
        temp2 = temp[['group']].drop_duplicates()['group'].tolist()
        ylabs = []
        for i in range(len(temp2)):
            k = int(((len(data[['product']].drop_duplicates())-1)/2)-0.5)
            if i>0:
                ax.axhline(i*len(data[['product']].drop_duplicates())-0.5, c='#c5c5c5', lw=0.5)
            name = ''
            for j in range(k):
                name += '\n'
            ylabs.append(name + temp2[i])
            for j in range(len(data[['product']].drop_duplicates())-1):
                ylabs.append('')
        ax.set_yticklabels(ylabs)
        plt.legend(bbox_to_anchor=(1.3, 0.65))
        #ax.set_ylim(-1.5, 5)
        # save figure
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_style2_T_' + group + '_' + str(year) + '.png', bbox_inches='tight', dpi=200)
        plt.show()
        
# make plot for all households with error bars flipped hue and y - flipped
for group in results_og[['group_var']].drop_duplicates()['group_var'].tolist():
    data = cp.copy(results_og)
    data = data.loc[data['group_var'] == group].drop('group_var', axis=1).drop_duplicates()
    data['product_2'] = data['group'] + data['product']
    data = data.sort_values('product_2')
    data['ci_low'] = data['elasticity'] - data['ci_low']
    data['ci_up'] = data['ci_up'] - data['elasticity']
    
    for year in years:
        temp = data.loc[data['year'] == year]
        fig, ax = plt.subplots(figsize=(len(data[['group']].drop_duplicates()), 5))
        # Add household groups
        plt.errorbar(y=temp['elasticity'], x=temp['product_2'],
                     yerr=np.array([temp['ci_low'], temp['ci_up']]),
                     capsize=0, ls='none', color='k', linewidth=0.5)
        sns.scatterplot(ax=ax, data=temp, x='product_2', y='elasticity', hue='product', s=50, 
                        palette='colorblind', edgecolor='black', linewidth=0.2)
        # Add other details
        ax.axhline(0, linestyle='--', c='black', lw=0.5)
        ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
        # organise legend
        # x labels
        #ax.tick_params(axis='x', labelrotation=90)
        temp2 = temp[['group']].drop_duplicates()['group'].tolist()
        xlabs = []
        for i in range(len(temp2)):
            k = int(((len(data[['product']].drop_duplicates())-1)/2)-0.5)
            if i>0:
                ax.axvline(i*len(data[['product']].drop_duplicates())-0.5, c='#c5c5c5', lw=0.5)
            name = ''
            for j in range(k):
                name += '\n'
            xlabs.append(name + temp2[i])
            for j in range(len(data[['product']].drop_duplicates())-1):
                xlabs.append('')
        ax.set_xticklabels(xlabs, rotation=90)
        plt.legend(bbox_to_anchor=(1.3, 0.65))
        #ax.set_ylim(-1.5, 5)
        # save figure
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_style2_' + group + '_' + str(year) + '.png', bbox_inches='tight', dpi=200)
        plt.show()
        
# make plot for all households with error bars flipped hue and y - flipped
maxmin = results_og.describe()['elasticity']
for group in results_og[['group_var']].drop_duplicates()['group_var'].tolist():
    data = cp.copy(results_og)
    data = data.loc[data['group_var'] == group].drop('group_var', axis=1).drop_duplicates()
    data['ci_low'] = data['elasticity'] - data['ci_low']
    data['ci_up'] = data['ci_up'] - data['elasticity']
    data = data.sort_values(['product', 'group_cat'])
    
    for year in years:
        temp = data.loc[data['year'] == year]
        fig, ax = plt.subplots(figsize=(len(data[['group']].drop_duplicates()), 5))
        # Add household groups
        sns.barplot(ax=ax, data=temp, x='group', y='elasticity', hue='product',
                        palette='colorblind', edgecolor='black', linewidth=0.2)
        # Add other details
        ax.axhline(0, linestyle='--', c='black', lw=0.5)
        ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
        # organise legend
        plt.ylim(maxmin['min']*0.9, maxmin['max']*1.1)
        plt.xticks(rotation=90)
        plt.legend(bbox_to_anchor=(1.3, 0.65))
        # save figure
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_all_households_styleBar_' + group + '_' + str(year) + '.png', bbox_inches='tight', dpi=200)
        plt.show()
