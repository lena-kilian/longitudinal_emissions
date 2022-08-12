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
import LCFS_import_data_function as lcfs_import
import pysal as ps


pop = 'hhld_oecd_equ'

if pop == 'no people':
    axis = 'tCO$_{2}$e / capita'
else:
    axis = 'tCO$_{2}$e / adult'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

raw_data = pd.read_csv(wd + 'data/processed/Longitudinal_model/model_data_2007-09_from_R.csv')
raw_data['year'] = raw_data['year_before'].map({1:2007, 0:2009})

count_keep = [(x, 'count') for x in ['oac_1', 'oac_2', 'oac_3', 'oac_4', 'oac_5', 'oac_6', 'oac_7',
              'gor_1', 'gor_2', 'gor_3', 'gor_4', 'gor_5', 'gor_6', 'gor_7', 'gor_8', 'gor_9', 'gor_10', 'gor_11', 'gor_12',
              'relative_hhld']]

mean_keep = [(x, 'mean') for x in ['No_adult_male', 'No_adult_female']]

raw_data_summary = raw_data.groupby(['age_group', 'year']).describe()[count_keep + mean_keep]



# regression results
cats = ['Food_and_Drinks', 'Other_consumption', 'Recreation_culture_and_clothing', 'Housing_water_and_waste', 
        'Electricity_gas_liquid_and_solid_fuels', 'Private_and_public_road_transport', 'Air_transport', 'Total_ghg']
results = pd.DataFrame(columns=['Cat'])
for cat in cats:
    temp = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Regression/Regression_' + cat + '_ses.csv')
    temp['Cat'] = cat
    results = results.append(temp)
results['p_var'] = ''
results.loc[results['Pr...t..'] < 0.05, 'p_var'] = '*'
results.loc[results['Pr...t..'] < 0.01, 'p_var'] = '**'

results['variable'] = results['variable'].str.replace(':', ' x ')

check = results[['Cat', 'variable', 'Estimate', 'weighted', 'p_var']].drop_duplicates()
temp = results[['Cat', 'weighted', 'adjR2']].drop_duplicates().rename(columns={'adjR2':'Estimate'})
temp['variable'] = 'adj. R2'

check = check.append(temp)\
    .set_index(['Cat', 'variable', 'weighted']).unstack(['Cat']).reset_index()\
        .swaplevel(axis=1).sort_index(axis=1, ascending=True)

