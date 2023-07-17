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
import statsmodels.api as sm
from statsmodels.formula.api import ols

res = stat()

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'
    
axis = 'tCO$_{2}$e/SPH'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':12})

comparisons = ['2007-2009_cpi', '2019-2020_cpi'] # '2007-2009', '2019-2020', 

years = []
for comp in comparisons:
    years.append(int(comp[:4]))
    years.append(int(comp[5:-4]))

group_dict = dict(zip(['All', '18-29', '30-49', '50-64', '65-74', '75+', 
                       0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ,'Other'], 
                      ['All housheolds', 'Age 18-29', 'Age 30-49', 'Age 50-64', 'Age 65-74', 'Age 75+',
                       'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest', 'Other']))

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
    for comp in comparisons:
        if str(year) in comp:
            ref_year = int(comp[:4])
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

for comp in comparisons:
    check3[comp] = check3[comp.split('-')[1]] - check3[comp.split('-')[0] + '_cpi']

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
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/change_plot_all_' + comp + '.png',
                dpi=200, bbox_inches='tight')
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
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/change_plot_pos_' + comp + '.png',
                dpi=200, bbox_inches='tight')
    plt.show()
    
for comp in comparisons:
    plot_data = check4.set_index('group')[comp][order]
    plot_data.plot(kind='bar', stacked=True, figsize=(7.5, 5), cmap=my_cmap)
    plt.xlabel('Household Group'); plt.ylabel('Change in ' + axis)
    plt.title(comp)
    ymin = pd.DataFrame(plot_data.stack()); ymin = ymin.loc[ymin[0] < 0]
    ymin = ymin.sum(axis=0, level=0).min() * 1.1
    plt.ylim(ymin[0], 0)
    plt.axhline(0, c='k', linestyle=':')
    plt.axvline(0.5, c='k'); plt.axvline(5.5, c='k')
    plt.legend(bbox_to_anchor = (1,1))
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/change_plot_neg_' + comp + '.png',
                dpi=200, bbox_inches='tight')
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

anova_data = pd.DataFrame(columns=['year'])
for year in years:
    temp = pc_ghg[year]
    temp['year'] = year
    temp = temp.loc[temp.index.repeat(temp['pop_mod'].astype(int))]
    anova_data = anova_data.append(temp)
for comp in comparisons:
    anova_data[comp] = False
    anova_data.loc[(anova_data['year'].str[:4].isin([comp.split('-')[0], comp.split('-')[1][:4]]) == True), comp] = True

anova_data = anova_data.set_index(['case', 'year', 'age_group_hrp', 'income_group'] + comparisons)[vars_ghg].stack().reset_index()\
    .rename(columns={'level_' + str(4+len(comparisons)):'product', 0:'GHG'})
anova_data['all'] = 'all'

results = pd.DataFrame(columns=['product'])
results_noninteract = pd.DataFrame(columns=['product'])
for cat in vars_ghg:
    for comp in comparisons:
        #perform the repeated measures ANOVA
        temp = anova_data.loc[(anova_data['product'] == cat) & (anova_data[comp] == True)]
        mod = 'GHG ~ C(year)'
        model = ols(mod, data=temp).fit()
        
        yr1 = comp.split('-')[0] + '_cpi'
        yr2 = comp.split('-')[1]
        
        diff = temp.groupby('year').mean()
        diff = diff.loc[yr2, 'GHG'] - diff.loc[yr1, 'GHG']
        
        temp = pd.DataFrame(sm.stats.anova_lm(model, typ=2))[['PR(>F)']]
        temp.columns = ['p-value']
        temp['group1'] = yr1; temp['group2'] = yr2
        
        temp['Diff'] = diff
        temp['product'] = cat
        temp['hhd_group'] = 'All'
        temp['comp'] = comp
        
        results_noninteract = results_noninteract.append(temp)
        
        for hhd_group in ['age_group_hrp', 'income_group']:
            #perform the repeated measures ANOVA
            temp = anova_data.loc[(anova_data['product'] == cat) & (anova_data[comp] == True)]\
                .sort_values(hhd_group)
            temp['group'] = temp[hhd_group]
            mod = 'GHG ~ C(year) + C(group) + C(year):C(group)'
            model = ols(mod, data=temp).fit()
            
            # group
            res.tukey_hsd(df=temp, res_var='GHG', xfac_var='group', anova_model=mod)
            temp2 = res.tukey_summary
            temp2['Diff'] = temp2['Diff'] *-1
            temp2['product'] = cat; temp2['hhd_group'] = hhd_group; temp2['comp'] = comp
            results_noninteract = results_noninteract.append(temp2)
            
            # year
            res.tukey_hsd(df=temp, res_var='GHG', xfac_var='year', anova_model=mod)
            temp2 = res.tukey_summary
            temp2['Diff'] = temp2['Diff'] *-1
            temp2['product'] = cat; temp2['hhd_group'] = hhd_group; temp2['comp'] = comp
            results_noninteract = results_noninteract.append(temp2)
            
            # interaction
            res.tukey_hsd(df=temp, res_var='GHG', xfac_var=['year', 'group'], anova_model=mod)
            temp2 = res.tukey_summary[['group1', 'group2', 'p-value', 'Diff']]
            temp2['Diff'] = temp2['Diff'] *-1
            temp2['product'] = cat; temp2['hhd_group'] = hhd_group; temp2['comp'] = comp
            results = results.append(temp2)
            
        print(comp)
    print(cat)
        

results_noninteract_summary = results_noninteract.set_index(['product', 'hhd_group', 'group1', 'group2', 'comp'])\
    [['Diff', 'p-value']].dropna(how='any')
results_noninteract_summary['sig'] = ' '
results_noninteract_summary.loc[results_noninteract_summary['p-value'] < 0.05, 'sig'] = '*'
results_noninteract_summary.loc[results_noninteract_summary['p-value'] < 0.01, 'sig'] = '**'
    
results_noninteract_summary = results_noninteract_summary[['Diff', 'sig']].unstack(level=['hhd_group', 'comp', 'group1', 'group2'])\
    .T.reset_index().sort_values(['hhd_group', 'comp', 'group1', 'group2', 'level_0'])\
        .set_index(['hhd_group', 'comp', 'group1', 'group2', 'level_0']).T.loc[order + ['Total']]
        
results_noninteract_pct = results_noninteract.set_index(['product', 'hhd_group', 'group1', 'group2', 'comp'])\
    [['Diff', 'p-value']].dropna(how='any')
results_noninteract_pct['sig'] = 0
results_noninteract_pct.loc[results_noninteract_pct['p-value'] < 0.05, 'sig'] = 1
results_noninteract_pct['count'] = 1
results_noninteract_pct = results_noninteract_pct.groupby(['hhd_group', 'comp', 'product']).sum()[['sig', 'count']]
results_noninteract_pct['pct'] = results_noninteract_pct['sig'] / results_noninteract_pct['count'] * 100
results_noninteract_pct = results_noninteract_pct[['pct']].unstack(level='product').T.droplevel(axis=0, level=0).loc[order + ['Total']]

results['year_1'] = [x[0] for x in results['group1']]
results['year_2'] = [x[0] for x in results['group2']]

results['group_1'] = [str(x[1]) for x in results['group1']]
results['group_2'] = [str(x[1]) for x in results['group2']]

results.index = list(range(len(results)))


results_all = results.loc[(results['hhd_group'] == 'All')].dropna(how='any')
results_all['sig'] = ' '
results_all.loc[results_all['p-value'] < 0.05, 'sig'] = '*'
results_all.loc[results_all['p-value'] < 0.01, 'sig'] = '**'
results_all = results_all.set_index(['product', 'comp'])[['sig', 'Diff']].unstack(level='comp')\
    .loc[['Total'] + order].swaplevel(axis=1)
    
results_all.to_csv(wd + 'Longitudinal_Emissions/outputs/anova_result.csv')


results_age = results.loc[(results['hhd_group'] == 'age_group_hrp') & 
                          ((results['group_1'] == results['group_2']) | (results['year_1'] == results['year_2']))]
results_age['type'] = 'group'
results_age.loc[results_age['group_1'] == results_age['group_2'], 'type'] = 'year'
results_age.loc[results_age['type'] == 'group', 'comp'] = results_age['year_1']
results_age.loc[results_age['type'] == 'year', 'comp'] = results_age['group_1']

results_age.loc[results_age['type'] == 'year', 'group_1'] = results_age['year_1']
results_age.loc[results_age['type'] == 'year', 'group_2'] = results_age['year_2']

results_age = results_age.rename(columns={'year_1':'year_2', 'year_2':'year_1'})

res_age_yr = results_age.loc[results_age['type'] == 'year'].set_index(['product', 'comp', 'year_1', 'year_2'])[['p-value', 'Diff']]
res_age_yr['sig'] = ' '
res_age_yr.loc[res_age_yr['p-value'] < 0.05, 'sig'] = '*'
res_age_yr.loc[res_age_yr['p-value'] < 0.01, 'sig'] = '**'
res_age_yr = res_age_yr[['Diff', 'sig']].unstack(['comp', 'year_1', 'year_2']).T.reset_index()\
    .sort_values(['comp', 'year_1', 'year_2', 'level_0']).set_index(['comp', 'year_1', 'year_2', 'level_0'])\
        .T.loc[order + ['Total']]


results_age = results_age[['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type', 'p-value']]

results_age_summary = cp.copy(results_age)
results_age['count'] = 1
results_age['sig'] = 0; results_age.loc[results_age['p-value'] < 0.05, 'sig'] = 1
results_age_summary = results_age.groupby(['hhd_group', 'product', 'type']).sum()[['sig', 'count']]
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

res_inc_yr = results_inc.loc[results_inc['type'] == 'year'].set_index(['product', 'comp', 'year_1', 'year_2'])[['p-value', 'Diff']]
res_inc_yr['sig'] = ' '
res_inc_yr.loc[res_inc_yr['p-value'] < 0.05, 'sig'] = '*'
res_inc_yr.loc[res_inc_yr['p-value'] < 0.01, 'sig'] = '**'
res_inc_yr = res_inc_yr[['Diff', 'sig']].unstack(['comp', 'year_1', 'year_2']).T.reset_index()\
    .sort_values(['comp', 'year_1', 'year_2', 'level_0']).set_index(['comp', 'year_1', 'year_2', 'level_0'])\
        .T.loc[order + ['Total']]


results_inc = results_inc[['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type', 'p-value']]
results_inc_summary = cp.copy(results_inc)
results_inc['count'] = 1
results_inc['sig'] = 0; results_inc.loc[results_inc['p-value'] < 0.05, 'sig'] = 1
results_inc_summary = results_inc.groupby(['hhd_group', 'product', 'type']).sum()[['sig', 'count']]
results_inc_summary['pct'] = results_inc_summary['sig'] / results_inc_summary['count'] * 100
results_inc_summary = results_inc_summary[['pct']].unstack('product')

results_inc_year = results_inc.loc[results_inc['type'] == 'year'].set_index(['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type'])\
    .unstack(['product'])
    
results_inc_group = results_inc.loc[results_inc['type'] == 'group'].set_index(['product', 'hhd_group', 'group_1', 'group_2', 'comp', 'type'])\
    .unstack(['product'])
    
    
results_summary = results_age_summary.droplevel(axis=1, level=0).reset_index()\
    .append(results_inc_summary.droplevel(axis=1, level=0).reset_index())

#results_summary2 =results_summary.groupby(['hhd_group', 'type']).mean().T

check = results_summary.set_index(['hhd_group', 'comp', 'type'])[order]

check_total = results_summary.set_index(['hhd_group', 'comp', 'type'])[['Total']]

for var_type in ['year', 'group']:
    temp = results_summary.loc[results_summary['type'] == var_type].set_index(['hhd_group', 'comp', 'type']).stack()\
        .reset_index().rename(columns={0:'pct'})
    sns.barplot(data=temp, x='comp', y='pct', hue='product')
    

res_yr = pd.DataFrame(res_age_yr.join(res_inc_yr).unstack()).unstack(level='level_0').droplevel(axis=1, level=0)[['sig']].reset_index()

res_yr['year_1'] = [int(x[:4]) for x in res_yr['year_1']]
res_yr['year_2'] = [int(x[:4]) for x in res_yr['year_2']]

res_yr['min'] = res_yr[['year_1', 'year_2']].min(1)
res_yr['max'] = res_yr[['year_1', 'year_2']].max(1)

res_yr['year'] = res_yr['min'].astype(str) + '-' + res_yr['max'].astype(str) + '_cpi'


check5 = check3.stack().reset_index().rename(columns={0:'Diff'})
check5['year_1'] = [x[:4] + '_cpi' for x in check5['year']]

group_dict2 = {group_dict[x]:x for x in list(group_dict.keys())}
check5['comp'] = check5['group'].map(group_dict2).astype(str)
check5.loc[check5['comp'].str.len() == 1, 'comp'] = check5['comp'] + '.0'


res_yr = res_yr.merge(check5, on=['year', 'product', 'comp'], how='left')
res_yr['year'] = res_yr['max'].astype(str) + ' - ' + res_yr['min'].astype(str)
res_yr = res_yr.set_index(['hhd_group', 'group', 'product', 'year'])[['Diff', 'sig']].unstack(level=['hhd_group', 'group', 'year'])
res_yr = res_yr.T.reset_index().sort_values(['hhd_group', 'group', 'year', 'level_0'])\
    .set_index(['hhd_group', 'group', 'year', 'level_0']).T.loc[order + ['Total']]