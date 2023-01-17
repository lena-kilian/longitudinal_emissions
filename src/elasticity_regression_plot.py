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


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

years = list(range(2001, 2020))

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':12})

results = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')
results['year_str'] = ['Year ' + str(x) for x in results['year']]
results = results.loc[results['cpi'] == 'cpi']

product_dict = {'Recreation, culture, and clothing':'Recreation,\nculture, and\nclothing',
                'Housing, water and waste':'Housing,\nwater and\nwaste',
                'Electricity, gas, liquid and solid fuels':'Electricity,\ngas, liquid\nand solid\nfuels',
                'Private and public road transport':'Private and\npublic road\ntransport',
                'Food and Drinks':'Food and\nDrinks',
                'Other consumption':'Other\nconsumption',
                'Air transport':'Air transport',
                'Total':'Total'}

results = results.loc[(results['group'].isin(['All households', 'Other', 'Household with children', '0']) == False)].dropna(how='any')

results['group_cat'] = results['group'].astype('category').cat.reorder_categories(
    ['all_households', 
     '18-29', '30-49', '50-64', '65-74', '75+', 
     'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])

results['product_cat'] = results['product'].astype('category').cat.reorder_categories(
	['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
    'Private and public road transport', 'Air transport', 'Recreation, culture, and clothing', 
    'Other consumption', 'Total'])

results_og = results.loc[results['year'] != 'all'].sort_values(['product_cat', 'group_cat'])
results_og['year'] = results_og['year'].astype(int)
results_og = results_og.loc[results_og['year'].isin(years) == True]
results_all_years = results.loc[results['year'] == 'all'].sort_values(['product_cat', 'group_cat'])


# make plot for all years with error bars
data = cp.copy(results_all_years)
data['ci_low'] = data['elasticity'] - data['ci_low']
data['ci_up'] = data['ci_up'] - data['elasticity']

def func(x,y,h,lb,ub, **kwargs):
    data = kwargs.pop("data")
    # from https://stackoverflow.com/a/37139647/4124317
    errLo = data.pivot(index=x, columns=h, values=lb)
    errHi = data.pivot(index=x, columns=h, values=ub)
    err = []
    for col in errLo:
        err.append([errLo[col].values, errHi[col].values])
    err = np.abs(err)
    p = data.pivot(index=x, columns=h, values=y)
    p.plot(kind='bar',yerr=err,ax=plt.gca(), **kwargs, capsize=2)


col_list = ['#396B98', '#BA8A38', '#48896C', '#AE662E', '#B985B2', '#B69474', 
            '#E9BADE', '#949494', '#EAE159', '#6FB2E4']
for group in data[['group_var']].drop_duplicates()['group_var']:      
    temp = data.loc[(data['group_var'] == group)].sort_values(['group_cat', 'product_cat'])
    if group == 'all':
        temp['group_cat'] = temp['group_cat'].str.replace('all_households', 'All')
    temp['product_cat'] = temp['product_cat'].map(product_dict)
    l = len(temp[['group']].drop_duplicates()['group'])
    
    g = sns.FacetGrid(temp, col='year', size=5, aspect=2) 
    g.map_dataframe(func, 'product_cat', 'elasticity', 'group_cat', 'ci_low', 'ci_up',
                    color=col_list, edgecolor='black', linewidth=0.2, width=0.85) 
    g.add_legend()
    plt.axhline(0, linestyle='--', c='black', lw=0.5)
    plt.axhline(1, linestyle='--', c='black', lw=0.5)
    plt.ylim(-0.275, 4.1)
    plt.ylabel('Income elasticity of emissions')
    plt.xlabel('')
    #plt.title('                                                                                                                                                                              ')

    # save figure
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_allyears_' + group + '.png', bbox_inches='tight', dpi=200)
    plt.show()
