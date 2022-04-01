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

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))

years = list(range(2001, 2019))

 
# import data
hhd_ghg = {}; pc_ghg = {}; people = {}
for year in years:
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv')
    pc_ghg[year] = hhd_ghg[year].set_index(['case']).loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year]['no people weighted'])
    people[year] = hhd_ghg[year].set_index(['case']).loc[:,:'hhd_comp3']

hhd_name = ['hhd_comp3']

data = pd.DataFrame(columns=['case', 'family_code', 'var', 'year', 'CCP1', 'ghg'])

for item in hhd_name:
    for year in [2007, 2008, 2009]:
        temp2 = people[year][[item]].rename(columns={item:'family_code'})
        temp = pc_ghg[year].join(temp2).set_index('family_code', append=True).loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
        temp['Total_ghg'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].sum(axis=1)
        temp = temp.rename(columns=cat_dict)
        temp = temp.sum(axis=1, level=0).stack().reset_index().rename(columns={'level_2':'CCP1', 0:'ghg'})
        temp['year'] = year
        temp['var'] = item
        data = data.append(temp)
        print(year)
    print(item)
    
       
for item in hhd_name:
    temp2 = data.loc[(data['var'] == item) & (data['year'] >= 2007) & (data['year'] <= 2009)]
    med = temp2.groupby(['year', 'family_code']).median().rename(columns={'ghg':'median'}).reset_index()
    temp2 = temp2.merge(med, on = ['year', 'family_code']).sort_values('median', ascending=False)
    product_list = data[['CCP1']].drop_duplicates()['CCP1']
    for i in range(len(product_list)):
        product = product_list[i]
        temp = temp2.loc[(temp2['CCP1'] == product)]
        fig, ax = plt.subplots(figsize=(8, 8))
        sns.boxplot(ax=ax, data=temp, hue='year', x='ghg', y='family_code')
        plt.title(product)
        xmax = [15, 12.5, 10, 3.5, 27.5, 30, 8, 100][i]
        #xmax=25
        plt.xlim(0, xmax)
        plt.savefig(r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/Longitudinal_Emissions/outputs/Explore_plots/' + item + '_' + product + '.png',
                    bbox_inches='tight')
        plt.show()

    
        #fig, ax = plt.subplots(figsize=(10,50))
        #sns.stripplot(ax=ax, data=temp, hue='year', x='ghg', y='family_code')
        #plt.title(product)
        #plt.savefig(r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/Longitudinal_Emissions/outputs/Explore_plots/JITTER_' + item + '_' + product + '.png', 
        #            bbox_inches='tight')
        #plt.show()
  