#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Import hhld expenditure data and adjust from 2020

@author: lenakilian

Next run: LCFS_import_data_function.py
"""

import pandas as pd
import LCFS_import_data_function as lcfs_import
import copy as cp
import pysal as ps

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

pop = 'hhld_oecd_mod' #'hhld_oecd_equ' #'no people' # change this to oecd equivalised scale if needed  #

# Load LCFS data
dvhh_file = wd + 'data/raw/LCFS/2019-2020/tab/2019-2020_dvhh_ukanon.tab'
dvper_file = wd + 'data/raw/LCFS/2019-2020/tab/2019-2020_dvper_ukanon.tab'

lcfs_2019 = lcfs_import.import_lcfs(2019, dvhh_file, dvper_file).drop_duplicates()
lcfs_2019 = lcfs_2019.reset_index()
lcfs_2019.columns = [x.lower() for x in lcfs_2019.columns]
lcfs_2019 = lcfs_2019.set_index('case') 

# OECD household equivalent scales
# https://www.oecd.org/economy/growth/OECD-Note-EquivalenceScales.pdf
temp = cp.copy(lcfs_2019)
temp['18+'] = temp['no people'] - temp['people aged <18']
temp['hhld_oecd_mod'] = 0
temp.loc[temp['18+'] > 0, '18+'] = temp['18+'] - 1
temp.loc[temp['18+'] == 0, 'people aged <18'] = temp['people aged <18'] - 1
temp['hhld_oecd_equ'] = temp['hhld_oecd_mod']
# OECD-modified scale
temp['hhld_oecd_mod'] = 1 + (temp['18+'] * 0.5) + (temp['people aged <18'] * 0.3)
# OECD equivalence scale
temp['hhld_oecd_equ'] = 1 + (temp['18+'] * 0.7) + (temp['people aged <18'] * 0.5)
lcfs_2019 = lcfs_2019.join(temp[['hhld_oecd_equ', 'hhld_oecd_mod']])

# edit variables where needed
lcfs_2019['pop'] = lcfs_2019['weight'] * lcfs_2019['no people']      
lcfs_2019['all'] = 'all'

lcfs_2019['pc_income'] = lcfs_2019['income anonymised'] / lcfs_2019[pop]
q = ps.Quantiles(lcfs_2019['pc_income'], k=10)
lcfs_2019['income_group'] = lcfs_2019['pc_income'].map(q).map(
    dict(zip([x for x in range(10)],
             ['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])))
lcfs_2019['pc_income'] = lcfs_2019['income anonymised'] / lcfs_2019['no people']

lcfs_2019['age_group_hrp'] = '18 or younger'
for i in [[18, 29], [30, 49], [50, 64], [65, 74]]:
    lcfs_2019.loc[lcfs_2019['age hrp'] >= i[0], 'age_group_hrp'] = str(i[0]) + '-' + str(i[1])
lcfs_2019.loc[lcfs_2019['age hrp'] >= 80, 'age_group_hrp'] = '75+'

# calculate weighted means
results = pd.DataFrame(columns=['pop'])
groups = []
for item in ['age_group_hrp', 'income_group', 'all']: #'hhd_type','gor modified', 
    # generate temp df
    temp = cp.copy(lcfs_2019)
    vars_ghg = ['income anonymised'] + temp.loc[:, '1.1.1.1':'12.5.3.5'].columns.tolist()
    temp = temp[vars_ghg + ['weight', 'pop', item]].set_index(item).apply(lambda x: pd.to_numeric(x, errors='coerce')).reset_index()
    # calculate weighted means
    # household level
    temp[vars_ghg] = temp[vars_ghg].apply(lambda x: x * temp['weight'])
    temp = temp.groupby(item).sum()
    temp[vars_ghg] = temp[vars_ghg].apply(lambda x: x / temp['weight'])
    results = results.append(temp)
results_2019 = results[vars_ghg].T


multiplier = pd.read_excel(wd + 'data/raw/LCFS/LCFS_aggregated_2020.xlsx', sheet_name='Multipliers_ccp4', header=0, index_col=0).fillna(0)
multiplier.index = [str(x) for x in multiplier.index]

groups = results_2019.columns.tolist()
results_2020 = cp.copy(results_2019)
for item in groups:
    results_2020 = results_2020.join(multiplier[[item]], rsuffix='_m')
    results_2020[item] = results_2020[item] * results_2020[item + '_m']
    
results_2020 = results_2020[groups].T

# add demographic info
temp = pd.read_excel(wd + 'data/raw/LCFS/LCFS_aggregated_2020.xlsx', sheet_name='pop', header=0, index_col=0).T
results_2020 = results_2020.join(temp)

results_2020['pop'] = results_2020['weight'] * results_2020['no people']

# save as is, all values already in 2019 values, because we only used 
results_2020.to_csv(wd + 'data/raw/LCFS/LCFS_aggregated_2020_adjusted.csv')

