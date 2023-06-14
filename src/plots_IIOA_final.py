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

res = stat()

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'
    
axis = 'tCO$_{2}$e/SPH'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':12})

years = [2007, 2009, 2019, 2020]

group_dict = dict(zip(['All', '18-29', '30-49', '50-64', '65-74', '75+', 
                       0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ,'Other'], 
                      ['All housheolds', 'Age 18-29', 'Age 30-49', 'Age 50-64', 'Age 65-74', 'Age 75+',
                       'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest', 'Other']))

comparisons = ['2007-2009_cpi', '2019-2020_cpi'] # '2007-2009', '2019-2020', 
  
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
    if year < 2010:
        ref_year = 2007
    else:
        ref_year = 2019
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

summary['group'] = pd.Categorical(summary['group'], 
                                  categories=['All housheolds', 
                                              'Age 18-29', 'Age 30-49', 'Age 50-64', 'Age 65-74', 'Age 75+',
                                              'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'],
                                  ordered=True)

check = summary.loc[(summary['hhd_group'] == 'All') & (summary['product'] == 'Total')]
check2 = summary.loc[(summary['hhd_group'] == 'All')].set_index(['year', 'product', 'hhd_group', 'group'])[['mean']].unstack('product')

check3 = summary.set_index(['year', 'product', 'hhd_group', 'group'])[['mean']].unstack('year').droplevel(axis=1, level=0)

#check3['2007-2009'] = check3['2009'] - check3['2007']
#check3['2019-2020'] = check3['2020'] - check3['2019']
check3['2007-2009_cpi'] = check3['2009_cpi'] - check3['2007_cpi']
check3['2019-2020_cpi'] = check3['2020_cpi'] - check3['2019_cpi']

check3 = check3.drop(years, axis=1)

# order = ['Food and non-alcoholic drinks', 'Eating and drinking out',
#          'Private transport', 'Public transport', 'Air transport',
#          'Clothing and footwear', 'Recreation and culture', 'Accommodation services and package holidays',
#          'Housing, water and waste', 'Electricity, gas, liquid and solid fuels',
#          'Other goods and services']

# order = vars_ghg[:-1]

order = ['Food and non-alcoholic drinks', 'Eating and drinking out',
         'Private transport', 'Public transport', 'Air transport',
         'Clothing and footwear', 'Recreation and culture', 'Accommodation services and package holidays',
         'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 'Furnishing and home maintenance',
         'Healthcare', 'Other goods and services']




check4 = check3[comparisons].loc[order].T.stack(level='product').T.reset_index()

cmap = matplotlib.cm.get_cmap('tab20c')
cmap = [matplotlib.colors.rgb2hex(cmap(x)) for x in range(cmap.N)]

my_cmap = [cmap[0], cmap[2], # Food
           cmap[4], cmap[5], cmap[7], # Transport
           cmap[8], cmap[9], cmap[10], # Free time
           cmap[12], cmap[13], cmap[14], # Housing
           cmap[16], cmap[18]] # Other
my_cmap=LinearSegmentedColormap.from_list(my_cmap, my_cmap)     

# plots differences
for comp in comparisons:
    plot_data = check4.set_index('group')[comp][order]
    plot_data.plot(kind='bar', stacked=True, figsize=(7.5, 5), cmap=my_cmap)
    plt.xlabel('Household Group'); plt.ylabel('Change in ' + axis)
    plt.title(comp)
    plt.axhline(0, c='k', linestyle=':')
    plt.axvline(0.5, c='k'); plt.axvline(5.5, c='k')
    plt.legend(bbox_to_anchor = (1,1))
    plt.show()
    
for comp in comparisons:
    plot_data = check4.set_index('group')[comp][order]
    plot_data.plot(kind='bar', stacked=True, figsize=(7.5, 5), cmap=my_cmap)
    plt.xlabel('Household Group'); plt.ylabel('Change in ' + axis)
    plt.title(comp)
    ymax = pd.DataFrame(plot_data.stack()); ymax = ymax.loc[ymax[0] > 0]
    ymax = ymax.sum(axis=0, level=0).max() * 1.1
    plt.ylim(0, ymax[0])
    plt.axhline(0, c='k', linestyle=':')
    plt.axvline(0.5, c='k'); plt.axvline(5.5, c='k')
    plt.legend(bbox_to_anchor = (1,1))
    plt.show()

# plots ghg
'''
summary['comparison'] = 'None'; summary['year_order'] = 'None'
for comp in comparisons:
    summary.loc[(summary['year'].astype(str) == comp[:4]) | (summary['year'].astype(str) == comp[-4:]), 'comparison'] = comp
    summary.loc[(summary['year'].astype(str) == comp[:4]), 'year_order'] = 'first'
    summary.loc[(summary['year'].astype(str) == comp[-4:]), 'year_order'] = 'last'
    
summary = summary.loc[summary['comparison'] != 'None']
    
for cat in vars_ghg:
    for comp in comparisons:
        plot_data = summary.loc[(summary['comparison'] == comp) & (summary['product'] == cat) & (summary['group'] != 'Other')]\
            .sort_values(['hhd_group', 'group'])
        
        fig, ax = plt.subplots(figsize=(15, 5))
        sns.barplot(ax=ax, data=plot_data, x='group', y='mean', hue='year')
        plt.title(cat + ' - ' + comp)
'''

# ANOVA

import statsmodels.api as sm
from statsmodels.formula.api import ols

anova_data = pd.DataFrame(columns=['year'])
for year in years:
    temp = pc_ghg[year]
    temp['year'] = year
    anova_data = anova_data.append(temp)
anova_data['yr_group'] = '2019-2020_cpi'
anova_data.loc[(anova_data['year'] == '2007_cpi') |
               (anova_data['year'] == '2009_cpi'), 'yr_group'] = '2007-2009_cpi'

anova_data = anova_data.set_index(['case', 'year', 'yr_group', 'age_group_hrp', 'income_group'])[vars_ghg[:-1]].stack().reset_index()\
    .rename(columns={'level_5':'product', 0:'GHG'})
anova_data['all'] = 'all'

results = pd.DataFrame(columns=['product'])
for cat in vars_ghg[:-1]:
    for comp in comparisons:
        #perform the repeated measures ANOVA
        temp = anova_data.loc[(anova_data['product'] == cat) & (anova_data['yr_group'] == comp)]
        mod = 'GHG ~ C(year)'
        model = ols(mod, data=temp).fit()
        
        temp = pd.DataFrame(sm.stats.anova_lm(model, typ=2))[['PR(>F)']]
        temp.columns = ['p-value']
        temp['group1'] = (comp.split('-')[0], comp.split('-')[1][:-4]); temp['group2'] = temp['group1']
        
        temp['product'] = cat; temp['hhd_group'] = 'All'; temp['comp'] = comp
        
        results = results.append(temp)
        for hhd_group in ['age_group_hrp', 'income_group']:
            #perform the repeated measures ANOVA
            temp = anova_data.loc[(anova_data['product'] == cat) & (anova_data['yr_group'] == comp)]
            temp['group'] = temp[hhd_group]
            mod = 'GHG ~ C(year) + C(group) + C(year):C(group)'
            model = ols(mod, data=temp).fit()
            
            #res.tukey_hsd(df=temp, res_var='GHG', xfac_var='group', anova_model=mod)
            #res.tukey_summary
            
            #res.tukey_hsd(df=temp, res_var='GHG', xfac_var='year', anova_model=mod)
            #res.tukey_summary
            
            res.tukey_hsd(df=temp, res_var='GHG', xfac_var=['year', 'group'], anova_model=mod)
            temp = res.tukey_summary[['group1', 'group2', 'p-value']]
            
            temp['product'] = cat; temp['hhd_group'] = hhd_group; temp['comp'] = comp
            
            results = results.append(temp)
        

results['year_1'] = [x[0] for x in results['group1']]
results['year_2'] = [x[0] for x in results['group2']]

results['group_1'] = [str(x[1]) for x in results['group1']]
results['group_2'] = [str(x[1]) for x in results['group2']]

results.index = list(range(len(results)))

results_age = results.loc[(results['hhd_group'] == 'age_group_hrp') & 
                          ((results['group_1'] == results['group_2']) | (results['year_1'] == results['year_2']))]
results_age['type'] = 'group'
results_age.loc[results_age['group_1'] == results_age['group_2'], 'type'] = 'year'
results_age.loc[results_age['type'] == 'group', 'comp'] = results_age['year_1']
results_age.loc[results_age['type'] == 'year', 'comp'] = results_age['group_1']

results_age.loc[results_age['type'] == 'year', 'group_1'] = results_age['year_1']
results_age.loc[results_age['type'] == 'year', 'group_2'] = results_age['year_2']

results_age = results_age[['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type', 'p-value']]

results_age_summary = cp.copy(results_age)
results_age['count'] = 1
results_age['sig'] = 0; results_age.loc[results_age['p-value'] < 0.05, 'sig'] = 1
results_age_summary = results_age.groupby(['hhd_group', 'comp', 'product', 'type']).sum()[['sig', 'count']]
results_age_summary['pct'] = results_age_summary['sig'] / results_age_summary['count'] * 100
results_age_summary = results_age_summary[['pct']].unstack('product')

results_age_year = results_age.loc[results_age['type'] == 'year'].set_index(['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type'])\
    .unstack(['product'])
    
results_age_group = results_age.loc[results_age['type'] == 'group'].set_index(['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type'])\
    .unstack(['product'])



results_inc = results.loc[(results['hhd_group'] == 'income_group') & 
                          ((results['group_1'] == results['group_2']) | (results['year_1'] == results['year_2']))]
results_inc['type'] = 'group'
results_inc.loc[results_inc['group_1'] == results_inc['group_2'], 'type'] = 'year'
results_inc.loc[results_inc['type'] == 'group', 'comp'] = results_inc['year_1']
results_inc.loc[results_inc['type'] == 'year', 'comp'] = results_inc['group_1']

results_inc.loc[results_inc['type'] == 'year', 'group_1'] = results_inc['year_1']
results_inc.loc[results_inc['type'] == 'year', 'group_2'] = results_inc['year_2']

results_inc = results_inc[['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type', 'p-value']]
results_inc_summary = cp.copy(results_inc)
results_inc['count'] = 1
results_inc['sig'] = 0; results_inc.loc[results_inc['p-value'] < 0.05, 'sig'] = 1
results_inc_summary = results_inc.groupby(['hhd_group', 'comp', 'product', 'type']).sum()[['sig', 'count']]
results_inc_summary['pct'] = results_inc_summary['sig'] / results_inc_summary['count'] * 100
results_inc_summary = results_inc_summary[['pct']].unstack('product')

results_inc_year = results_inc.loc[results_inc['type'] == 'year'].set_index(['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type'])\
    .unstack(['product'])
    
results_inc_group = results_inc.loc[results_inc['type'] == 'group'].set_index(['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type'])\
    .unstack(['product'])
    
    
results_summary = results_age_summary.reset_index().append(results_inc_summary.reset_index())
    
    
'''
for item in ['year_1', 'year_2']:
    results[item] = results[item].map({'2007_cpi':'before', '2009_cpi':'after', '2019_cpi':'before', '2020_cpi':'after'})

results_years = results.loc[(results['year_1'] != results['year_2']) & (results['group_1'] == results['group_2'])]\
    .set_index(['product', 'hhd_group', 'group_1', 'comp', 'year_1', 'year_2'])[['p-value']].unstack(level=['year_1', 'product'])



results_groups = results.loc[(results['year_1'] == results['year_2']) & (results['group_1'] != results['group_2'])]\
    .set_index(['product', 'hhd_group', 'group_1', 'group_2', 'year_1'])[['p-value']].unstack(level=['product'])

for item in ['year_1', 'year_2']:
    results[item] = results[item].map({'2007_cpi':'before', '2009_cpi':'after', '2019_cpi':'before', '2020_cpi':'after'})

results_years = results.loc[(results['year_1'] != results['year_2']) & (results['group_1'] == results['group_2'])]\
    .set_index(['product', 'hhd_group', 'group_1', 'comp', 'year_1', 'year_2'])[['p-value']].unstack(level=['year_1', 'product'])
'''
