#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

calculating elasticities -- using 2007 mutipliers and expenditure adjusted to 2007 cpi

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
summary_var = '50%' # 'mean' # 

if pop == 'no people':
    axis = 'tCO$_{2}$e / capita'
else:
    axis = 'tCO$_{2}$e / adult'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'


products = cat_lookup[['Category']].drop_duplicates()['Category'].tolist()

fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

filenames = ["'Household_emissions_2007_multipliers_2009_wCPI.csv'", 
             "'Household_emissions_2009.csv'"]

# import data
hhd_ghg = {}
for i in range(2):
    filename = filenames[i]
    name = ['wCPI', 'wo'][i]
    hhd_ghg[name] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/' + eval(filename)).set_index(['case'])

difference = (hhd_ghg['wCPI'].loc[:,'1.1.1.1':'12.5.3.5'] - hhd_ghg['wo'].loc[:,'1.1.1.1':'12.5.3.5'])


mean_diff = difference.mean()
