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
import pickle
import pysal as ps
import matplotlib


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
pop = 'hhld_oecd_equ' #'no people' # change this to oecd equivalised scale if needed  #

years = list(range(2001, 2020))

vars_ghg = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 'Air transport', 
            'Recreation, culture, and clothing', 'Other consumption', 'Total']

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':12})

results = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')
results['year_str'] = ['Year ' + str(x) for x in results['year']]

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

anova = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_anova.csv')  


# make plot for all years with error bars
results['ci_low'] = results['elasticity'] - results['ci_low']
results['ci_up'] = results['ci_up'] - results['elasticity']

# calculate intensities
# import ghg
data_ghg = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
data_ghg.loc[:,'Food and Drinks':'Total'] = data_ghg.loc[:,'Food and Drinks':'Total'].apply(lambda x:x*data_ghg['no people']*data_ghg['weight'])

# import spend
cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'

lcfs_og = {}

for year in years:
    # regular
    lcfs_og[year] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv').set_index('case')
    order = lcfs_og[year].columns
    # with cpi
    lcfs_og[str(year) + '_cpi'] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '_wCPI_ref2007.csv').set_index('case')[order]

lcfs = {}
intensities = pd.DataFrame(columns=['year'])
for year in list(lcfs_og.keys()):
    lcfs_temp = cp.copy(lcfs_og[year])
    # classify age range of hrp
    lcfs_temp['age_group_hrp'] = 'Other'
    for i in [[18, 29], [30, 49], [50, 64], [65, 74]]:
        lcfs_temp.loc[lcfs_temp['age hrp'] >= i[0], 'age_group_hrp'] = str(i[0]) + '-' + str(i[1])
    lcfs_temp.loc[lcfs_temp['age hrp'] >= 80, 'age_group_hrp'] = '75+'
    
    # OECD household equivalent scales
    # https://www.oecd.org/economy/growth/OECD-Note-EquivalenceScales.pdf
    temp = cp.copy(lcfs_temp)
    temp['<16'] =  temp['people aged <18'] - temp['people aged 16-17']
    temp['16+'] = temp['no people'] - temp['<16']
    temp['hhld_oecd_mod'] = 0
    temp.loc[temp['16+'] > 0, 'hhld_oecd_mod'] = 1
    temp['hhld_oecd_equ'] = temp['hhld_oecd_mod']
    # OECD-modified scale
    temp['hhld_oecd_mod'] = temp['hhld_oecd_mod'] + ((temp['16+'] - 1) * 0.5) + (temp['<16'] * 0.3)
    lcfs_temp = lcfs_temp.join(temp[['hhld_oecd_mod']])
    # OECD equivalence scale
    temp['hhld_oecd_equ'] = temp['hhld_oecd_equ'] + ((temp['16+'] - 1) * 0.7) + (temp['<16'] * 0.5)
    lcfs_temp = lcfs_temp.join(temp[['hhld_oecd_equ', '16+']])

    lcfs_temp['pc_income'] = lcfs_temp['income anonymised'] / lcfs_temp[pop]
    q = ps.Quantiles(lcfs_temp['pc_income'], k=10)
    lcfs_temp['income_group'] = lcfs_temp['pc_income'].map(q)
    
    lcfs_temp['All households'] = 'all_households'
    
    lcfs[year] = pd.DataFrame(columns=['group_var'])
    for group in ['All households', 'age_group_hrp', 'income_group']:
        temp = lcfs_temp.copy()
        temp.loc[:,'1.1.1.1':'12.5.3.5'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x:x*temp['weight'])
        temp['income_anonymised'] = temp['income anonymised'] * temp['weight']
        temp['age_hrp'] = temp['age hrp'] * temp['weight']
        temp['pop_oecd'] = temp['hhld_oecd_equ'] * temp['weight']
        temp = temp.groupby(group).sum()
        temp['income_anonymised'] = temp['income_anonymised'] / temp['pop_oecd']
        temp['age_hrp'] = temp['age_hrp'] / temp['weight']
        keep = temp.loc[:,'1.1.1.1':'12.5.3.5'].columns.tolist() + ['income_anonymised', 'age_hrp', 'weight', 'pop_oecd']
        temp = temp[keep].reset_index().rename(columns={group:'group'})
        temp['group_var'] = group
        if group == 'income_group':
            temp['group'] = temp['group'].map(dict(zip(list(range(10)), ['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])))
        lcfs[year] = lcfs[year].append(temp.reset_index())
    
    # group products
    lcfs[year] = lcfs[year].rename(columns=cat_dict).sum(axis=1, level=0)
    lcfs[year]['Total'] = lcfs[year][vars_ghg[:-1]].sum(1)

    temp = cp.copy(lcfs[year])
    if 'cpi' in str(year):
        temp['cpi'] = 'cpi'
        temp['year'] = int(year[:4])
    else:
        temp['cpi'] = 'regular'
        temp['year'] = int(year)
    intensities = intensities.append(temp.reset_index())

temp = cp.copy(intensities)
temp['income_anonymised'] = temp['income_anonymised'] * temp['pop_oecd']
temp['age_hrp'] = temp['age_hrp'] * temp['weight']
temp = temp.groupby(['group_var', 'group', 'cpi']).sum().reset_index()
temp['income_anonymised'] = temp['income_anonymised'] / temp['pop_oecd']
temp['age_hrp'] = temp['age_hrp'] / temp['weight']
temp['year'] = 'all'
intensities = intensities.append(temp)

intensities['year'] = intensities['year'].astype(str)
data_ghg['year'] = data_ghg['year'].astype(str)
data_ghg['cpi'] = data_ghg['cpi'].str.replace('with_cpi', 'cpi')
data_ghg['group'] = data_ghg['group'].str.replace('All households', 'all_households')
    
data_int = intensities.set_index(['group', 'year', 'cpi', 'income_anonymised', 'age_hrp'])[vars_ghg]
data_all = data_ghg.set_index(['group', 'year', 'cpi'])[vars_ghg].join(data_int, rsuffix='_exp', lsuffix='_ghg')
for item in vars_ghg:
    data_all[item] = data_all[item + '_ghg'] / (data_all[item + '_exp'] * 52) *1000
    
data_all = data_all[vars_ghg].stack().reset_index().rename(columns={'level_5':'product', 0:'intensities'})

data = data_all.merge(results, on=['group', 'product', 'year', 'cpi'], how='outer').drop_duplicates()

data.to_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_results_with_intensities.csv')

"""
### plot
data_plot = data.loc[data['year'] == 'all']
sns.scatterplot(data=data_plot, x='elasticity', y='intensities', hue='group', style='product')
plt.legend(bbox_to_anchor=(1, 1)); plt.show()

for item in vars_ghg:
    temp = data_plot.loc[data_plot['product'] == item]
    sns.scatterplot(data=temp, x='elasticity', y='intensities', hue='group')
    plt.legend(bbox_to_anchor=(1, 1)); 
    plt.title(item)
    plt.show()
"""

data_plot = data.loc[(data['year'] != 'all') & (data['cpi'] == 'regular') & (data['product'] == 'Total')]
for group in ['all', 'age_group_hrp', 'income_group']:
    temp = data_plot.loc[data_plot['group_var'] == group]
    fig, ax = plt.subplots()
    sns.kdeplot(ax=ax, data=temp, x='elasticity', hue='group')
    plt.show()

for cpi in ['regular']:
    data_plot = data.loc[(data['year'] != 'all') & (data['cpi'] == cpi)]
    for group in ['all', 'age_group_hrp', 'income_group', 'intensities']:
        fig, ax = plt.subplots(figsize=(9, 3))
        if group != 'intensities':
            temp = data_plot.loc[data_plot['group_var'] == group].sort_values(['product_cat', 'group_cat'])
            temp['product_cat'] = temp['product_cat'].map(product_dict)
            temp['group'] = temp['group'].replace('all_households', 'All households')
            if group == 'all':
                sns.boxplot(ax=ax, data=temp, y='elasticity', x='product_cat', hue='group', palette='colorblind', 
                            linewidth=0.8, width=0.25)
            else:
                sns.boxplot(ax=ax, data=temp, y='elasticity', x='product_cat', hue='group', palette='colorblind', 
                            linewidth=0.8)
            plt.setp(ax.artists, edgecolor = 'k')
            plt.axhline(0, linestyle='-', c='black', lw=0.5)
            plt.axhline(1, linestyle='--', c='black', lw=0.5)
            plt.ylabel('Elasticity')
            plt.xlabel('')
            plt.ylim(-0.5, 5.5)
            #plt.xticks(rotation=90)
        else:
            temp2 = temp.groupby(['product_cat', 'year']).mean()[['intensities']].reset_index()
            sns.boxplot(ax=ax, data=temp2, y='intensities', x='product_cat', linewidth=1, width=.25)
            plt.setp(ax.artists, edgecolor = 'k', facecolor='w')
            ax.set_ylabel('Intensity (kgCO$_{2}$e / GBP)')
            plt.ylim(0, 37.5)
        for i in range(7):
            plt.axvline(i+0.5, linestyle=':', c='grey', lw=0.5)
            
        if group in ['age_group_hrp', 'income_group']:
            anova_temp = anova.loc[anova['group_var'] == group].set_index('product')
            prods = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
                     'Private and public road transport', 'Air transport', 'Recreation, culture, and clothing', 
                     'Other consumption', 'Total']          
            for i in range(len(prods)):
                text = anova_temp.loc[prods[i], 'sig']
                plt.text(i-0.25, 5.1, text)
            
        # save figure
        plt.legend(bbox_to_anchor=(1.5, 1)); 
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_boxplots_' + group + '_' + cpi + '.png', bbox_inches='tight', dpi=200)
        plt.show()
        
for cpi in ['regular', 'cpi']:
    data_plot = data.loc[(data['year'] != 'all') & (data['cpi'] == cpi)]
    for group in ['all', 'age_group_hrp', 'income_group']:
        temp = data_plot.loc[data_plot['group_var'] == group].sort_values(['product_cat', 'group_cat'])
        temp['product_cat'] = temp['product_cat'].map(product_dict)
        temp['group'] = temp['group'].replace('all_households', 'All households')
        fig, ax = plt.subplots(figsize=(9, 3))
        sns.boxplot(ax=ax, data=temp, y='elasticity', x='product_cat', hue='group', palette='colorblind', linewidth=0.8)
        plt.legend(bbox_to_anchor=(1.5, 1)); 
        plt.axhline(0, linestyle='-', c='black', lw=0.5)
        plt.axhline(1, linestyle='--', c='black', lw=0.5)
        for i in range(7):
            plt.axvline(i+0.5, linestyle=':', c='grey', lw=0.5)
        plt.ylabel('Elasticity')
        plt.xlabel('')
        plt.ylim(-0.5, 5)
        #plt.xticks(rotation=90)
        
        if cpi == 'with_cpi':
            temp2 = temp.loc[temp['year'] == '2007'].groupby('product_cat').mean()[['intensities']].reset_index()
            temp2['CI'] = 'Carbon Intensity\n(mean value)'
        else:
            temp2 = temp.groupby('product_cat').mean()[['intensities']].reset_index()
            #temp2 = temp.groupby(['product_cat', 'year']).mean()[['intensities']].reset_index()
            temp2['CI'] = 'Carbon Intensity\n(mean value)'
        ax2 = ax.twinx()
        sns.scatterplot(ax=ax2, data=temp2, y='intensities', x='product_cat', hue='CI', palette=sns.color_palette(['red']))
        ax2.set_ylabel('Intensity (kgCO$_{2}$e / GBP)')
        plt.ylim(-2.2, 22)
        plt.legend(bbox_to_anchor=(1.5, -0.5)); 
        
        # save figure
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_boxplots_' + group + '_' + cpi + '_w_intensities.png', bbox_inches='tight', dpi=200)
        plt.show()
    