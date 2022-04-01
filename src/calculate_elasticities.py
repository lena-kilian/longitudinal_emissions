#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import copy as cp
import numpy as np
import LCFS_import_data_function as lcfs_import


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))

years = list(range(2001, 2019))

lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))

pop_type = 'no people weighted'

# import data
hhd_ghg = {}; pc_ghg = {}; people = {}; hhdspend = {}
for year in years:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    hhdspend[year] = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    hhdspend[year]['Total'] = hhdspend[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)
    hhdspend[year] = hhdspend[year].rename(columns=cat_dict).sum(axis=1, level=0)
    
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv')
    hhd_ghg[year]['pop'] = hhd_ghg[year]['weight'] * hhd_ghg[year][pop_type]
    hhd_ghg[year]['Income anonymised'] = hhd_ghg[year]['Income anonymised'] * hhd_ghg[year]['weight'] /  hhd_ghg[year]['pop']
    
    hhd_ghg[year]['hhd_comp3'] = 'All'
    
    pc_ghg[year] = hhd_ghg[year].set_index(['case']).loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x * hhd_ghg[year]['weight'] / hhd_ghg[year]['pop'])
    people[year] = hhd_ghg[year][hhd_ghg[year].loc[:,:'hhd_comp3'].columns.tolist() + ['pop']].set_index(['case'])

hhd_name = ['hhd_comp3']

    
# calulate means
products = cat_lookup[['Category']].drop_duplicates()['Category'].tolist() + ['Total']
col_list = [x + '_ghg' for x in products] + [x + '_exp' for x in products] + ['Income anonymised']

year = 2007
temp = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
temp['Total'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].sum(axis=1)
temp = temp.rename(columns=cat_dict).sum(axis=1, level=0)\
        .join(people[year][['Income anonymised', 'pop', 'hhd_comp3']])\
            .join(hhdspend[year][products], lsuffix='_ghg', rsuffix='_exp')
temp[col_list] = temp[col_list].apply(lambda x: x * temp['pop'])
temp = temp.groupby(['hhd_comp3']).sum()
temp[col_list] = temp[col_list].apply(lambda x: x / temp['pop'])

data_07 = cp.copy(temp)


year = 2009
temp = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
temp['Total'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].sum(axis=1)
temp = temp.rename(columns=cat_dict).sum(axis=1, level=0)\
        .join(people[year][['Income anonymised', 'pop', 'hhd_comp3']])\
            .join(hhdspend[year][products], lsuffix='_ghg', rsuffix='_exp')
temp[col_list] = temp[col_list].apply(lambda x: x * temp['pop'])
temp = temp.groupby(['hhd_comp3']).sum()
temp[col_list] = temp[col_list].apply(lambda x: x / temp['pop'])

data_09 = cp.copy(temp)

# calculate elasticities
hhd_comp = data_09.index.tolist()

results = pd.DataFrame(columns=['hhd_comp', 'inc_elasticity', 'product', 
                                'income_diff', 'income_mean', 'ghg_diff', 'ghg_mean',
                                'income_fraction', 'ghg_fraction'])
for p in products:
    prod = p +'_ghg'
    for hhd in hhd_comp:
        ghg_diff = data_09.loc[hhd, prod] - data_07.loc[hhd, prod]
        ghg_mean = (data_09.loc[hhd, prod] + data_07.loc[hhd, prod]) / 2
        inc_diff = data_09.loc[hhd, 'Income anonymised'] - data_07.loc[hhd, 'Income anonymised']
        inc_mean = (data_09.loc[hhd, 'Income anonymised'] + data_07.loc[hhd, 'Income anonymised']) / 2
        
        temp = pd.DataFrame(columns=['hhd_comp', 'inc_elasticity', 'product'], index=[0])
        temp['hhd_comp'] = hhd
        temp['product'] = p
        temp['income_diff'] = inc_diff
        temp['income_mean'] = inc_mean
        temp['ghg_diff'] = ghg_diff
        temp['ghg_mean'] = ghg_mean
        
        temp['income_fraction'] = temp['income_diff'] / temp['income_mean']
        temp['ghg_fraction'] = temp['ghg_diff'] / temp['ghg_mean']
        
        temp['inc_elasticity'] = (ghg_diff / ghg_mean) / (inc_diff / inc_mean)

        results = results.append(temp)
        
results_exp = pd.DataFrame(columns=['hhd_comp', 'exp_elasticity', 'product'])

for p in products:
    prod = p +'_ghg'
    exp = p +'_exp'
    for hhd in hhd_comp:
        ghg_diff = data_09.loc[hhd, prod] - data_07.loc[hhd, prod]
        exp_diff = data_09.loc[hhd, exp] - data_07.loc[hhd, exp]

        ghg_mean = (data_09.loc[hhd, prod] + data_07.loc[hhd, prod]) / 2
        exp_mean = (data_09.loc[hhd, exp] + data_07.loc[hhd, exp]) / 2
        
        
        temp = pd.DataFrame(columns=['hhd_comp', 'exp_elasticity', 'product'], index=[0])
        temp['hhd_comp'] = hhd
        temp['product'] = p
        
        temp['exp_elasticity'] = (ghg_diff / ghg_mean) / (exp_diff / exp_mean)
        results_exp = results_exp.append(temp)
              
all_results = results.set_index(['hhd_comp', 'product'])[['inc_elasticity']]\
    .join(results_exp.set_index(['hhd_comp', 'product'])[['exp_elasticity']])
