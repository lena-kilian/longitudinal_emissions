#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Create boxplots and table summary for 2007 and 2009 - with adjusted to 2007 CPI and using 2007 multipliers

@author: lenakilian
"""

import pandas as pd
import copy as cp
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import LCFS_import_data_function as lcfs_import
import pysal as ps


pop = 'no people'

axis = 'tCO$_{2}$e / capita'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category_2']))

cat_cats = {'Electricity, gas, liquid and solid fuels':'Housing',
            'Private transport':'Transport',
            'Other consumption':'Other',
            'Food and Drinks':'Food',
            'Air transport':'Transport',
            'Recreation and culture goods':'Other',
            'Eating and drinking out':'Food',
            'Housing, water and waste':'Housing',
            'Clothing and Footwear':'Other',
            'Public road transport':'Transport',
            'Takeaway Meals':'Food',
            'Recreation and culture services':'Other'}

years = [[2007, 2009], [2019, 2020]]

# import data
pc_ghg = pd.DataFrame(columns=['year', 'year_group'])
for year_group in years:
    for year in year_group:
        if year_group == [2007, 2009]:
            temp = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2007_multipliers_' + str(year) + '_wCPI.csv')\
                .set_index(['case'])
            temp.loc[:,'1.1.1.1':'12.5.3.5'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x*temp['weight'])
            temp['pop'] = temp['weight'] * temp[pop]
            temp = pd.DataFrame(temp.sum(0)).rename(columns={0:'ghg'})
            temp = temp.loc['1.1.1.1':'12.5.3.5',:]/temp.loc['pop', 'ghg']
            temp = temp.rename(index=cat_dict).sum(axis=0, level=0).reset_index().rename(columns={'index':'Category'})
        else:
            temp = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2019_multipliers_' + str(year) + '_wCPI.csv')\
                .set_index(['case']).rename(columns=cat_dict).sum(axis=1, level=0).T.reset_index()\
                    .rename(columns={'index':'Category', 'pc_exp':'ghg'})
        temp['year'] = year
        temp['year_group'] = str(year_group[0]) + '-' + str(year_group[1])
        pc_ghg = pc_ghg.append(temp)


######################
# Boxplots 2007-2009 #
######################

order = pc_ghg.loc[pc_ghg['year'] == 2007].sort_values('ghg', ascending=False)['Category'].tolist()
pc_ghg['Category_order'] = pd.Categorical(pc_ghg['Category'], categories=order, ordered=True)

for year_group in years:
    group = str(year_group[0]) + '-' + str(year_group[1])
    plot_data = pc_ghg.loc[pc_ghg['year_group'] == group]
    fig, ax = plt.subplots(figsize=(5, 5))
    sns.barplot(ax=ax, data=plot_data, x='ghg', y='Category_order', hue='year', palette='RdBu', edgecolor='black')
    ax.set_xlabel(axis); ax.set_ylabel('')
    ax.set_xlim(0, 4)
    ax.legend(loc='lower right', title='Year')
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/boxplot_' + group + '.png', 
                bbox_inches='tight', dpi=200)
    plt.show()
    
# separate cats
temp = cp.copy(pc_ghg)
temp['Super_cats'] = temp['Category_order'].map(cat_cats)

for cat in temp[['Super_cats']].drop_duplicates()['Super_cats']:
    plot_data = temp.loc[temp['Super_cats'] == cat]
    # add 2015 to have white space
    temp2 = plot_data[['Category']].drop_duplicates()
    temp2['year'] = 2015
    temp2['ghg'] = 0
    l = len(temp2)
    plot_data = plot_data.append(temp2)
    # plot
    fig, ax = plt.subplots(figsize=(5, l))
    sns.barplot(ax=ax, data=plot_data, x='ghg', y='Category', hue='year', palette='RdBu', edgecolor='black')
    ax.set_xlabel(axis); ax.set_ylabel('')
    # remove 2015 from legend
    handles, labels = plt.gca().get_legend_handles_labels()
    order = [0, 1, 3, 4]
    ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order], bbox_to_anchor=(1, 1))
    for i in range(l-1):
        plt.axhline(y=i+0.5, color='k', linestyle='--', linewidth=1)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/boxplot_' + cat + '.png', 
                bbox_inches='tight', dpi=200)
    plt.show()
    
    
# differences
plot_data = cp.copy(temp)
plot_data['year'] = plot_data['year'].map({2007:'before', 2009:'after', 2019:'before', 2020:'after'})
plot_data = plot_data.set_index(['year', 'year_group', 'Category', 'Category_order', 'Super_cats'])\
    .unstack(level=['year', 'year_group']).droplevel(axis=1, level=0)
plot_data = plot_data['after'] - plot_data['before']
plot_data = plot_data.stack().reset_index().sort_values(['Super_cats', 'year_group']).rename(columns={0:'ghg_difference'})
#plot
fig, ax = plt.subplots(figsize=(5, 5))
sns.barplot(ax=ax, data=plot_data, x='ghg_difference', y='Category', hue='year_group', palette='RdBu', edgecolor='black')
ax.set_xlabel('Difference in ' + axis); ax.set_ylabel('')
ax.set_xlim(-1, 1)
ax.legend(bbox_to_anchor=(1.4, 1))
for i in [2, 4, 8]:
    plt.axhline(y=i+0.5, color='k', linestyle='--', linewidth=1)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/boxplot_differences.png', 
            bbox_inches='tight', dpi=200)
plt.show()
    

#########################
# Percentage bar charts #
#########################

temp = pc_ghg.set_index(['year', 'Category_order', 'Category']).drop(['year_group'], axis=1).unstack(['year'])
temp = temp.apply(lambda x:x/x.sum()*100).droplevel(axis=1, level=0).sort_values(2007, ascending=False)

start = [0 for j in range(len(temp.columns))]
for item in temp.index.tolist():
    plt.barh(left=start, width=temp.loc[item].tolist(), y=[str(x) for x in temp.columns])
    start += temp.loc[item]

# both years
temp = temp.stack().reset_index().rename(columns={0:'ghg'})
fig, ax = plt.subplots(figsize=(5, 5))
sns.barplot(ax=ax, data=temp, x='ghg', y='Category_order', hue='year', palette='RdBu', edgecolor='black')

# separate years
for year_group in years:
    group = str(year_group[0]) + '-' + str(year_group[1])
    plot_data = temp.loc[temp['year'].isin(year_group)==True]
    fig, ax = plt.subplots(figsize=(5, 5))
    sns.barplot(ax=ax, data=plot_data, x='ghg', y='Category_order', hue='year', palette='RdBu', edgecolor='black')
    ax.set_xlabel('Percentage of ' + axis); ax.set_ylabel('')
    ax.set_xlim(0, 35)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/boxplot_' + group + '_percent.png', 
                bbox_inches='tight', dpi=200)
    plt.show()

# separate cats
temp['Super_cats'] = temp['Category_order'].map(cat_cats)

for cat in temp[['Super_cats']].drop_duplicates()['Super_cats']:
    plot_data = temp.loc[temp['Super_cats'] == cat]
    # add 2015 to have white space
    temp2 = plot_data[['Category']].drop_duplicates()
    temp2['year'] = 2015
    temp2['ghg'] = 0
    l = len(temp2)
    plot_data = plot_data.append(temp2)
    # plot
    fig, ax = plt.subplots(figsize=(5, l))
    sns.barplot(ax=ax, data=plot_data, x='ghg', y='Category', hue='year', palette='RdBu', edgecolor='black')
    ax.set_xlabel('Percentage of ' + axis); ax.set_ylabel('')
    # remove 2015 from legend
    handles, labels = plt.gca().get_legend_handles_labels()
    order = [0, 1, 3, 4]
    ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order], bbox_to_anchor=(1, 1))
    for i in range(l-1):
        plt.axhline(y=i+0.5, color='k', linestyle='--', linewidth=1)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/boxplot_' + cat + '_percent.png', 
                bbox_inches='tight', dpi=200)
    plt.show()
