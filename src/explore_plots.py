#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Plots for all years

@author: lenakilian
"""

import pandas as pd
import copy as cp
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import LCFS_import_data_function as lcfs_import
import pysal as ps


pop = 'hhld_oecd_equ'

if pop == 'no people':
    axis = 'tCO$_{2}$e / capita'
else:
    axis = 'tCO$_{2}$e / adult'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'

fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = list(range(2001, 2019))

# import data
hhd_ghg = {}; pc_ghg = {}; people = {}; hhd_ghg_2007m = {}; pc_ghg_2007m= {}
for year in years:
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv').set_index(['case'])
    pc_ghg[year] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year][pop])
    people[year]['population'] = people[year][pop] * people[year]['weight']
    
    if year in [2007, 2008, 2009]:
        hhd_ghg_2007m[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2007_multipliers_' + str(year) + '.csv')\
            .set_index('case')
        pc_ghg_2007m[year] = hhd_ghg_2007m[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg_2007m[year][pop])
    
    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)


#######################
# Lineplots all years #
#######################


data = pd.DataFrame(columns=['year', 'Product Category', 'ghg'])
    
for year in years:
    temp = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
    temp = temp.rename(columns=cat_dict).sum(axis=1, level=0).join(people[year][[pop]])
    temp.loc[:,:'Air transport'] = temp.loc[:,:'Air transport'].apply(lambda x: x*temp[pop])
    temp = pd.DataFrame(temp.sum(0)).reset_index().rename(columns={'index':'Product Category', 0:'ghg'})
    temp['ghg'] = temp['ghg'] / temp.iloc[-1, -1]
    temp = temp.loc[temp['Product Category'] != pop]
    temp['year'] = year
    data = data.append(temp)
    print(year)
data['year'] = pd.to_datetime(data['year'], format="%Y")
    
# Plot
# Linegraph values
fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=data.reset_index(), x='year', y='ghg', hue='Product Category')
ax.set_ylabel('tCO$_{2}$e / adult'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs.png', bbox_inches='tight')
plt.show()

# Linegraph w/ percentage
data_pct = data.set_index(['year', 'Product Category']).unstack(level=[0])
values_01 = data_pct.iloc[:,0]
data_pct = data_pct.apply(lambda x: x/values_01*100).stack().reset_index()

fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=data_pct, x='year', y='ghg', hue='Product Category')
ax.set_ylabel('tCO$_{2}$e / adult'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.axhline(y=100, linestyle=':', color='k', lw=0.5)
plt.ylim(50,150)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_pct.png',
            bbox_inches='tight')
plt.show()
