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
import seaborn as sns
import matplotlib.pyplot as plt
import copy as cp

axis = 'tCO$_{2}$e / capita'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':11})

vars_ghg = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
            'Private and public road transport', 'Air transport', 
            'Recreation, culture, and clothing', 'Other consumption',
            'Total']

vars_ghg_dict = ['Food and\nDrinks', 'Housing, water\nand waste', 'Electricity, gas,\nliquid and solid fuels', 
                 'Private and public\nroad transport', 'Air transport', 
                 'Recreation, culture,\nand clothing', 'Other\nconsumption',
                 'Total']

group_dict = {'hhd_type':'Household Composition', 'age_group_hrp':'Age of HRP', 'gor modified':'Region', 
              'income_group':'Income Decile', 'all':'All'}


# import data
data_ghg = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
data_ghg = data_ghg.loc[(data_ghg['group'] != '0') & (data_ghg['group'] != 'Other')]
data_ghg['group'] = data_ghg['group'].str.replace('all_households', 'All households')

data_comp = data_ghg.loc[data_ghg['year'].isin(['2007', '2009', '2019', '2020']) == True]
data_comp['type'] = data_comp['year'].map({'2007':'2007-2009', '2009':'2007-2009', '2019':'2019-2020', '2020':'2019-2020'})
data_comp['year_type'] = data_comp['year'].map({'2007':'First year', '2009':'Last year', '2019':'First year', '2020':'Last year'})
#data_comp['index'] = list(range(len(data_comp)))

data_comp = data_comp.set_index(['type', 'year_type', 'cpi', 'group', 'group_var', 'pc'])[vars_ghg + ['pc_income']].unstack(level=['type', 'year_type'])\
    .swaplevel(axis=1).swaplevel(axis=1, i=0, j=1).swaplevel(axis=1, i=2, j=1)

for event in ['2007-2009', '2019-2020']:
    for product in vars_ghg + ['pc_income']:
        data_comp[('Difference', event, product)] = data_comp[('Last year', event, product)] - data_comp[('First year', event, product)]
        data_comp[('Percentage difference', event, product)] = data_comp[('Difference', event, product)] / data_comp[('First year', event, product)] * 100
        
data_comp = data_comp.stack().stack().reset_index()

order = ['All households', '18-29', '30-49', '50-64', '65-74', '75+', 'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest']
data_comp['group_cat'] = data_comp['group'].astype('category').cat.set_categories(order, ordered=True)

data_comp = data_comp.sort_values('group_cat')

check = data_comp.set_index(['cpi', 'group', 'group_var', 'level_4', 'type', 'group_cat', 'pc']).unstack(level='level_4').stack(level=0)[
    ['pc_income', 'Total', 'Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 'Private and public road transport', 
     'Air transport', 'Recreation, culture, and clothing', 'Other consumption']].reset_index().sort_values(['year_type', 'pc', 'cpi', 'type', 'group_cat'])