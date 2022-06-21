#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import copy as cp
import numpy as np
import LCFS_import_data_function as lcfs_import
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch
import pysal as ps

########################
# GET DATA FOR 07 & 09 #
########################

def get_data(var, year1, year2, cat_lookup, fam_code_lookup, hhd_ghg, pop_type, k):
    
    pc_ghg = {}; people={}
    for year in [year1, year2]:
        pc_ghg[year] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x * hhd_ghg[year]['weight'] / hhd_ghg[year]['pop'])
        people[year] = hhd_ghg[year][hhd_ghg[year].loc[:,:'new_desc'].columns.tolist() + ['pop']]
    
        people[year]['pc_income'] = people[year]['income anonymised'] / people[year][pop_type]
        q = ps.Quantiles(people[year]['pc_income'], k=k)
        people[year]['income_group'] = people[year]['pc_income'].map(q)
    
        people[year]['age_range'] = '18-29'
        for i in [30, 40, 50, 60, 70]:
            people[year].loc[people[year]['age of oldest person in household - anonymised'] > i, 'age_range'] = str(i) + '-' + str(i+9)
            people[year].loc[people[year]['age_range'] == '70-79', 'age_range'] = '70+'
            people[year].loc[people[year]['no people'] != 1, 'age_range'] = 'Other'
    
    
    # calulate means
    products = cat_lookup[['Category']].drop_duplicates()['Category'].tolist() + ['Total']
    col_list = products + ['income anonymised']
    
    cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))

    count = {}; data = {}
    
    for year in [year1, year2]:
        temp = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
        temp['Total'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].sum(axis=1)
        temp = temp.rename(columns=cat_dict).sum(axis=1, level=0)\
            .join(people[year][['income anonymised', 'pop', var]])

        if var == 'income_group':
            var_list = []
            for item in temp[var]:
                if item+1 < 10:
                    var_list.append('Decile 0' + str(item + 1))
                else:
                    var_list.append('Decile ' + str(item + 1))
            temp[var] = var_list
            temp = temp.sort_values(var)
        elif var == 'composition of household':
            code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == var]
            code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
            temp[var] = temp[var].map(code_dict)
    
        count_temp = temp.groupby(var).count()[['Total']]; count_temp.columns = ['count']
        temp[col_list] = temp[col_list].apply(lambda x: x * temp['pop'])
        temp = temp.groupby([var]).sum()
        temp[col_list] = temp[col_list].apply(lambda x: x / temp['pop'])

        data[year] = cp.copy(temp)
        count[year] = count_temp.join(data[year].loc[:,:'income anonymised'])
        count[year]['year'] = year
        
    count = count[year1].append(count[year2]).reset_index()
    count = count[[var, 'year', 'count', 'income anonymised', 'Total',
                  'Air transport', 'Electricity, gas, liquid and solid fuels', 'Food and Drinks', 'Housing, water and waste',
                  'Other consumption', 'Private and public road transport', 'Recreation, culture, and clothing']]

    return(data, count)


##########################
# CALCULATE ELASTICITIES #
##########################

def calc_elasticities(var, data, year1, year2, cat_lookup, hhd_ghg, pop_type, wd):
    data_07 = data[year1]
    data_09 = data[year2]
    
    products = cat_lookup[['Category']].drop_duplicates()['Category'].tolist() + ['Total']
    cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))

    hhd_comp = data_09.index.tolist()

    results = pd.DataFrame(columns=['hhd_comp', 'inc_elasticity', 'product', 'income_diff', 'income_mean', 'ghg_diff', 'ghg_mean', 
                                    'income_fraction', 'ghg_fraction'])
    # with variable
    for prod in products:
        for hhd in hhd_comp:
            ghg_diff = data_09.loc[hhd, prod] - data_07.loc[hhd, prod]
            ghg_mean = (data_09.loc[hhd, prod] + data_07.loc[hhd, prod]) / 2
            inc_diff = data_09.loc[hhd, 'income anonymised'] - data_07.loc[hhd, 'income anonymised']
            inc_mean = (data_09.loc[hhd, 'income anonymised'] + data_07.loc[hhd, 'income anonymised']) / 2
        
            temp = pd.DataFrame(columns=['hhd_comp', 'inc_elasticity', 'product'], index=[0])
            temp['hhd_comp'] = hhd
            temp['product'] = prod
            temp['income_diff'] = inc_diff
            temp['income_mean'] = inc_mean
            temp['ghg_diff'] = ghg_diff
            temp['ghg_mean'] = ghg_mean
        
            temp['income_fraction'] = temp['income_diff'] / temp['income_mean']
            temp['ghg_fraction'] = temp['ghg_diff'] / temp['ghg_mean']
        
            temp['inc_elasticity'] = (ghg_diff / ghg_mean) / (inc_diff / inc_mean)

            results = results.append(temp)
              
    all_results = results.set_index(['hhd_comp', 'product'])[['inc_elasticity']].reset_index()
    
    cols = hhd_ghg[year1].loc[:,'1.1.1.1':'12.5.3.5'].columns.tolist() + ['income anonymised']

    temp = hhd_ghg[year1][cols + [pop_type]]
    temp['year'] = 'ghg_' + str(year1)

    temp2 = hhd_ghg[year2][cols + [pop_type]]
    temp2['year'] = 'ghg_' + str(year2)

    temp = temp.append(temp2)
    temp['Total'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].sum(axis=1)
    temp = temp.rename(columns=cat_dict).sum(axis=1, level=0)

    cols = ['Food and Drinks', 'Other consumption', 'Recreation, culture, and clothing', 'Housing, water and waste', 
            'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 'Air transport', 'Total', 'income anonymised']

    temp[cols] = temp[cols].apply(lambda x: x*temp[pop_type])
    temp = temp.groupby('year').sum()
    temp = temp[cols].apply(lambda x: x/temp[pop_type]).T

    income_diff = temp.loc['income anonymised', 'ghg_' + str(year2)] - temp.loc['income anonymised', 'ghg_' + str(year1)]
    income_mean = (temp.loc['income anonymised', 'ghg_' + str(year2)] + temp.loc['income anonymised', 'ghg_' + str(year1)]) / 2

    temp['ghg_diff'] = temp['ghg_' + str(year2)] - temp['ghg_' + str(year1)]
    temp['ghg_mean'] = (temp['ghg_' + str(year2)] + temp['ghg_' + str(year1)]) / 2

    temp['inc_elasticity'] = (temp['ghg_diff'] / temp['ghg_mean']) / (income_diff / income_mean)
    temp['hhd_comp'] = 'All households'
    
    product_dict = {'Recreation, culture, and clothing':'Recreation,\nculture, and\nclothing',
                    'Housing, water and waste':'Housing, water\nand waste',
                    'Electricity, gas, liquid and solid fuels':'Electricity, gas,\nliquid and solid\nfuels',
                    'Private and public road transport':'Private and public\nroad transport',
                    'Food and Drinks':'Food and Drinks',
                    'Other consumption':'Other\nconsumption',
                    'Air transport':'Air transport'}
    
    title_dict = {'composition of household':'Household Composition', 'income_group':'Income Decile', 'age_range':'Age Range'}
    
    w=5; h=4

    fig, ax = plt.subplots(figsize=(w, h))
    ax.axhline(0, linestyle='--', c='black', lw=0.5)
    plot_data = all_results.loc[(all_results['product'] != 'Total') & (all_results['hhd_comp'] != 'Other')].sort_values(['product', 'hhd_comp'])
    plot_data['product'] = plot_data['product'].map(product_dict)
    sns.scatterplot(ax=ax, data=plot_data, x='product', y='inc_elasticity', style='hhd_comp', color='k', s=70)
    sns.set_palette(sns.color_palette(['#C54A43'])) # '#78AAC8'
    plot_data = temp.iloc[:-2,:].reset_index().rename(columns={'index':'product'}).sort_values(['product', 'hhd_comp'])
    plot_data['product'] = plot_data['product'].map(product_dict)
    sns.scatterplot(ax=ax, data=plot_data, x='product', y='inc_elasticity',  hue='hhd_comp', s=70)
    ax.tick_params(axis='x', labelrotation=90)
    ax.set_xlabel('')
    ax.set_ylabel('Income elasticity')
    #ax.set_ylim(-85, 20)
    
    handles, labels = plt.gca().get_legend_handles_labels()
    order = [len(handles) - 1] + list(range(len(handles) - 1))
    plt.legend([handles[i] for i in order], [labels[i] for i in order])
        
    sns.move_legend(ax,loc='upper left', bbox_to_anchor=(1.05, 0.98), title=title_dict[var])
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/Income_Elasticity_plots_reversed_' + var + '.png', bbox_inches='tight', dpi=200)

    fig, ax = plt.subplots(figsize=(w, h))
    ax.axhline(0, linestyle='--', c='black', lw=0.5)
    plot_data = all_results.loc[(all_results['product'] != 'Total') & (all_results['hhd_comp'] != 'Other')].sort_values(['product', 'hhd_comp'])
    plot_data['product'] = plot_data['product'].map(product_dict)
    sns.scatterplot(ax=ax, data=plot_data, x='product', y='inc_elasticity', style='hhd_comp', color='k', s=70)
    sns.set_palette(sns.color_palette(['#C54A43'])) # '#78AAC8'
    plot_data = temp.iloc[:-2,:].reset_index().rename(columns={'index':'product'}).sort_values(['product', 'hhd_comp'])
    plot_data['product'] = plot_data['product'].map(product_dict)
    sns.scatterplot(ax=ax, data=plot_data, x='product', y='inc_elasticity',  hue='hhd_comp', s=70)
    ax.tick_params(axis='x', labelrotation=90)
    ax.set_xlabel('')
    ax.set_ylabel('Income elasticity')
    ax.set_ylim(-10, 10)
    
    handles, labels = plt.gca().get_legend_handles_labels()
    order = [len(handles) - 1] + list(range(len(handles) - 1))
    plt.legend([handles[i] for i in order], [labels[i] for i in order])
    
    sns.move_legend(ax,loc='upper left', bbox_to_anchor=(1.05, 0.98), title=title_dict[var])
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/Income_Elasticity_plots_reversed_detail_' + var + '.png', bbox_inches='tight', dpi=200)
    
    return(all_results)


