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

# Load LCFS data
dvhh_file = wd + 'data/raw/LCFS/2019-2020/tab/2019-2020_dvhh_ukanon.tab'
dvper_file = wd + 'data/raw/LCFS/2019-2020/tab/2019-2020_dvper_ukanon.tab'

lcfs_2019 = lcfs_import.import_lcfs(2019, dvhh_file, dvper_file).drop_duplicates()
lcfs_2019 = lcfs_2019.reset_index()
lcfs_2019.columns = [x.lower() for x in lcfs_2019.columns]
lcfs_2019 = lcfs_2019.set_index('case') 

# edit variables where needed
lcfs_2019['pop'] = lcfs_2019['weight'] * lcfs_2019['no people']      
lcfs_2019['all'] = 'all'

lcfs_2019['pc_income'] = lcfs_2019['income anonymised'] / lcfs_2019['no people']
q = ps.Quantiles(lcfs_2019['pc_income'], k=10)
lcfs_2019['income_group'] = lcfs_2019['pc_income'].map(q).map(
    dict(zip([x for x in range(10)],
             ['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])))

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
    vars_ghg = temp.loc[:, '1.1.1.1':'12.5.3.5'].columns.tolist()
    temp = temp[vars_ghg + ['weight', 'pop', item]].set_index(item).apply(lambda x: pd.to_numeric(x, errors='coerce')).reset_index()
    # calculate weighted means
    # household level
    temp[vars_ghg] = temp[vars_ghg].apply(lambda x: x * temp['weight'])
    temp = temp.groupby(item).sum()
    temp[vars_ghg] = temp[vars_ghg].apply(lambda x: x / temp['pop'])
    results = results.append(temp)
results_2019 = results[vars_ghg].T
ccp3 = []
for item in results_2019.index:
    if item.count('.') > 2:
        x = str(item).split('.')[0] + '.' + str(item).split('.')[1] + '.' + str(item).split('.')[2]
    else:
        x = str(item)
    ccp3.append(x)
results_2019['COICOP3_code'] = ccp3

multiplier = pd.read_excel(wd + 'data/raw/LCFS/LCFS_aggregated_2020.xlsx', sheet_name='Multipliers', header=[1]).iloc[:,:23].fillna(0)
multiplier = results_2019.reset_index()[['index', 'COICOP3_code']].merge(multiplier, on='COICOP3_code', how='left').set_index('index')

groups = results_2019.columns.tolist()[:-1]
results_2020 = cp.copy(results_2019)
for item in groups:
    results_2020 = results_2020.join(multiplier[[item]], rsuffix='_m')
    results_2020[item] = results_2020[item] * results_2020[item + '_m']
    
results_2020 = results_2020[groups]

income = pd.read_excel(wd + 'data/raw/LCFS/LCFS_aggregated_2020.xlsx', sheet_name='Income', header=[0], index_col=0).fillna(0).T

results_2020 = results_2020.T.join(income)
results_2020['pop'] = results_2020['weight'] * results_2020['no people']


# load CPI corrector data
# adjust to CPI
ref_year = 2019 # choose year which to adjust expenditure to
# import cpi cat lookup
cpi_lookup = pd.read_excel(wd + 'data/processed/CPI_lookup.xlsx', sheet_name='Sheet4')
cpi_lookup['ccp_lcfs'] = [x.split(' ')[0] for x in cpi_lookup['ccp_lcfs']]
# import cpi data --> uses 2015 as base year, change to 2007
cpi = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0)\
    .loc[['2019', '2020']].T.dropna(how='all').astype(float)
#check = cp.copy(cpi)
cpi = cpi.apply(lambda x: x/cpi[str(ref_year)] * 100)
cpi['Type'] = [x.split(' ')[0] + ' ' + x.split(' ')[1] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Type'].isin(['CPI INDEX']) == True]
cpi['Reference_year'] = [x[-8:] for x in cpi.index.tolist()]
cpi = cpi.loc[cpi['Reference_year'].str.contains('=100') == True]
cpi['Product'] = [x.replace('CPI INDEX ', '').split(' ')[0] for x in cpi.index.tolist()]

hhdspend_cpi = cp.copy(results_2020)

cpi_dict = dict(zip(cpi_lookup['ccp_lcfs'], cpi_lookup['CPI_CCP4_index']))

# don't adjust income, as this is already in 2019 values

for item in hhdspend_cpi.loc[:,'1.1.1.1':'12.5.3.5'].columns:
    hhdspend_cpi[item] = hhdspend_cpi[item] * (100 / float(cpi.loc[cpi_dict[item], '2020'])) # check again that this is correct


# make sure that groups add up to average
var_list = hhdspend_cpi.loc[:,'1.1.1.1':'12.5.3.5'].columns.tolist() + ['income anonymised']
temp = cp.copy(hhdspend_cpi.set_index('group_var', append=True))
temp[var_list] = temp[var_list].apply(lambda x: x*temp['weight'])
temp = temp.join(temp[var_list].sum(axis=0, level=1), rsuffix='_sum')
for item in var_list:
    temp.loc[temp[item + '_sum'] == 0, item + '_sum'] = 0.01
    temp[item] = temp[item] / temp[item + '_sum'] * temp.loc[('all', 'All'), item + '_sum']
temp = temp[var_list].apply(lambda x: x/temp['weight'])

hhdspend_cpi = hhdspend_cpi.drop(var_list, axis=1).join(temp.droplevel(axis=0, level=1))

hhdspend_cpi.to_csv(wd + 'data/raw/LCFS/LCFS_aggregated_2020_adjusted_2.csv')

