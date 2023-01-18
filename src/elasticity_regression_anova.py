#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.anova import AnovaRM
import scipy.stats as stats

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
pop = 'hhld_oecd_equ' #'no people' # change this to oecd equivalised scale if needed  #

years = list(range(2001, 2020))

vars_ghg = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 'Air transport', 
            'Recreation, culture, and clothing', 'Other consumption', 'Total']

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':12})

results = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')
results['year'] = ['Year ' + str(x) for x in results['year']]

results = results.loc[
    (results['group'].isin(['All households', 'Other', 'Household with children', '0']) == False) & 
    (results['year'] != 'Year all')].dropna(how='any')

results['group_cat'] = results['group'].astype('category').cat.reorder_categories(
    ['all_households', 
     '18-29', '30-49', '50-64', '65-74', '75+', 
     'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])

results['product_cat'] = results['product'].astype('category').cat.reorder_categories(
	['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
    'Private and public road transport', 'Air transport', 'Recreation, culture, and clothing', 
    'Other consumption', 'Total'])

results = results.sort_values(['product_cat', 'group_cat'])

anova = pd.DataFrame(columns=['group_var', 'product'])
ttest = pd.DataFrame(columns=['group_var', 'product', 'group1', 'group2'])
for group in ['age_group_hrp', 'income_group']:
    for product in results[['product']].drop_duplicates()['product'].tolist():

        data = results.loc[(results['group_var']==group) & (results['product']==product)]\
            [['year', 'elasticity', 'group']].drop_duplicates()
            
        temp = (AnovaRM(data=data, depvar='elasticity', subject='year', within=['group']).fit()).anova_table
        temp['group_var'] = group
        temp['product'] = product
        anova = anova.append(temp)
        
        items = data[['group']].drop_duplicates()['group'].tolist()
        pairs = []
        for i in range(len(items)-1):
            group1 = items[i]
            for j in range(i+1, len(items)):
                group2 = items[j]
                pairs.append([group1, group2])
        
        for pair in pairs:
            group1 = pair[0]; group2 = pair[1]
            data2 = data.loc[data['group'].isin(pair)==True].set_index(['group', 'year'])\
                    .unstack(level='group').droplevel(axis=1, level=0)
            temp = pd.DataFrame(stats.ttest_rel(data2[group1], data2[group2])).T
            temp.columns = ['T-val', 'pval']
            temp['df'] = len(data2)-1
            temp['no_comp'] = len(pairs)
            
            temp['group_var'] = group
            temp['group1'] = group1
            temp['group2'] = group2
            temp['product'] = product
            
            ttest = ttest.append(temp)
            
ttest['bonferroni_cutoff'] = 0.05/ttest['no_comp']
ttest['bonferroni_sig'] = ''
ttest.loc[ttest['pval'] < ttest['bonferroni_cutoff'], 'bonferroni_sig'] = '*'
ttest.loc[ttest['pval'] < ttest['bonferroni_cutoff']/5, 'bonferroni_sig'] = '**'

anova['sig'] = ''
anova.loc[anova['Pr > F'] < 0.05, 'sig'] = 'p<0.05'
anova.loc[anova['Pr > F'] < 0.01, 'sig'] = 'p<0.01'


ttest_summary = {}
for group in ['age_group_hrp', 'income_group']:
    temp = ttest.loc[ttest['group_var']==group]
    ttest_summary[group] = temp.set_index(['product', 'group1', 'group2'])[['bonferroni_sig']].unstack(level='group2')
            
                
            
anova.to_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_anova.csv')  

ttest2 = ttest.set_index(['group_var', 'product', 'group1', 'group2'])[['T-val', 'df', 'pval', 'bonferroni_sig']].unstack(level='product')
ttest2 =ttest2.swaplevel(axis=1).T.sort_index().T
