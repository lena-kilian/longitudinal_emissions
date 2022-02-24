#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  9 09:19:27 2022

@author: lenakilian
"""

import copy as cp
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis'
oac_level = 'Supergroup'

first_year = 2014
last_year = 2018
years = range(first_year, last_year+1)

ghg = {year:pd.read_csv(wd + '/data/processed/GHG_Estimates/OAC_' + oac_level + '_' + str(year) + '.csv') for year in years}

lookup = pd.read_csv(wd + '/data/processed/LCFS/Meta/lcfs_lookup_longitudinal.csv')
lookup.index = [x.split(' ')[0] for x in lookup['ccp'].tolist()]

ghg_all = pd.DataFrame()
for year in years:
    ghg[year] = ghg[year].loc[ghg[year]['OAC_' + oac_level] != 0]
    ghg[year]['OAC_' + oac_level] = ghg[year]['OAC_' + oac_level].astype(str)
    ghg[year] = ghg[year].set_index('OAC_' + oac_level).T.join(lookup[['Supercategory', 'category_2']])\
        .groupby(['Supercategory', 'category_2']).sum()
    ghg[year]['year'] = year
    
    ghg_all = ghg_all.append(ghg[year])

ghg_all = ghg_all.set_index(['year'], append=True).stack().reset_index().rename(columns={'level_3':'OAC', 0:'ghg'})

# Plot
supercats = ghg_all[['Supercategory']].drop_duplicates()['Supercategory'].tolist()

for cat in supercats:
    temp = ghg_all.loc[(ghg_all['Supercategory'] == cat)]
    g = sns.FacetGrid(data=temp, row='category_2', hue='OAC')
    g.map(sns.lineplot, 'year', 'ghg')
    plt.show()
    