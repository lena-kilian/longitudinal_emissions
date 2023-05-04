#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Create boxplots and table summary for 2007 and 2009 - with adjusted to 2007 CPI and using 2007 multipliers

@author: lenakilian
"""

import pandas as pd
import copy as cp
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import LCFS_import_data_function as lcfs_import
import pysal as ps
from sys import platform

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'

pop = 'hhld_oecd_equ'

if pop == 'no people':
    axis = 'tCO$_{2}$e / capita'
else:
    axis = 'tCO$_{2}$e / adult'


cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'

fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = [2007, 2009]

lcf_years = dict(zip(years, ['2007', '2009']))

filename = "'Household_emissions_2007_multipliers_' + str(year) + '_wCPI.csv'"
#filename = "'Household_emissions_' + str(year) + '.csv'"

# import cpi data --> uses 2015 as base year, change to 2007
inflation = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0)\
    .loc[[str(x) for x in years], 'CPI INDEX 00: ALL ITEMS 2015=100']\
        .T.dropna(how='all').astype(float)
inflation = inflation.apply(lambda x: x/inflation[str(years[0])])

# import data
hhd_ghg = {}; pc_ghg = {}; people = {}
for year in years:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    income = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    income.columns = [x.lower() for x in income.columns]
    income = income[['income anonymised']].rename(columns={'income anonymised':'hhld_income'})
    
    # adjust for inflation if CPI used and 2007 m
    if filename.split("'")[-2] == '_wCPI.csv':
        income['hhld_income'] = income['hhld_income'] / inflation[str(year)]
    
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/' + eval(filename)).set_index(['case'])
    pc_ghg[year] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year][pop])
    people[year] = hhd_ghg[year].loc[:,:'1.1.1.1'].iloc[:,:-1].join(income[['hhld_income']])
    people[year]['pc_income'] = people[year]['hhld_income'] / people[year][pop]
    people[year]['population'] = people[year][pop] * people[year]['weight']

    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)
    
    # import age range and student status
    temp = pd.read_csv(wd + 'data/processed/LCFS/Socio-demographic/person_variables_' + str(year) + '.csv').set_index('case')
    people[year] = people[year].join(temp[['age_group', 'student_hhld']])
    #people[year]['age_group'] = people[year]['age_group'] + ' ' + people[year]['student_hhld'] 


# save results for regression
year1 = 2007; year2 = 2009
data = people[year1].reset_index().merge(pc_ghg[year1].rename(columns=cat_dict).sum(axis=1, level=0).reset_index(), on='case')
data['year'] = year1
temp = people[year2].reset_index().merge(pc_ghg[year2].rename(columns=cat_dict).sum(axis=1, level=0).reset_index(), on='case')
temp['year'] = year2
data = data.append(temp)
cols = cat_lookup[['Category']].drop_duplicates()['Category'].tolist()
data['Total'] = data[cols].sum(1)
for item in ['Composition of household']:
    var_dict = fam_code_lookup.loc[fam_code_lookup['Variable'] == item]
    var_dict = dict(zip(var_dict['Category_num'], var_dict['Category_desc']))
    data[item.lower()] = data[item.lower()].map(var_dict)
data['income_group'] = ['Decile ' + str(x+1) for x in data['income_group']]
data.to_csv(wd + 'data/processed/GHG_Estimates_LCFS/Regression_data.csv')
