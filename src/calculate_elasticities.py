#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import LCFS_import_data_function as lcfs_import
import calculate_elasticities_function as cef
import copy as cp


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]

cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))

fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = list(range(2001, 2019))

lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))

pop_type = 'no people weighted'

k = 5 # number of income quantiles

inflation_070809 = [0.96, 1, 1.04, 1.03]

year1 = 2007; year2 = 2009
# import data
hhd_ghg_2007m = {}; pc_ghg = {}; people = {}; hhdspend = {}; income = {}
for year in [year1, year2]:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    hhdspend[year] = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    hhdspend[year]['Total'] = hhdspend[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)
    hhdspend[year] = hhdspend[year].rename(columns=cat_dict).sum(axis=1, level=0)
    
    hhd_ghg_2007m[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2007_multipliers_' + str(year) + '.csv').set_index(['case'])
    hhd_ghg_2007m[year]['pop'] = hhd_ghg_2007m[year]['weight'] * hhd_ghg_2007m[year][pop_type]
    hhd_ghg_2007m[year]['income anonymised'] = hhd_ghg_2007m[year]['income anonymised'] * hhd_ghg_2007m[year]['weight'] /  hhd_ghg_2007m[year]['pop']
    hhd_ghg_2007m[year]['income anonymised'] = hhd_ghg_2007m[year]['income anonymised'] / inflation_070809[year-2007]

count = {}
for var in ['composition of household', 'income_group', 'age_range']:#, 'hhd_age_group']:
    # GET DATA FOR 07 & 09
    data, count[var] = cef.get_data(var, year1, year2, cat_lookup, fam_code_lookup, hhd_ghg_2007m, pop_type, k)
    # add difference
    count[var] = count[var].set_index(['year', var])
    temp = count[var].loc[2009] - count[var].loc[2007]
    temp['year'] = 'Difference'
    count[var] = count[var].append(temp.reset_index().set_index(['year', var]))
    # add percentage
    temp = count[var].loc['Difference'] / count[var].loc[2007] * 100
    temp['year'] = 'Percentage'
    count[var] = count[var].append(temp.reset_index().set_index(['year', var]))
    # CALCULATE ELASTICITIES
    all_results = cef.calc_elasticities(var, data, year1, year2, cat_lookup, hhd_ghg_2007m, pop_type, wd)

# save results for regression
data = hhd_ghg_2007m[year1].rename(columns=cat_dict).sum(axis=1, level=0).reset_index()
data['year'] = year1
temp = hhd_ghg_2007m[year2].rename(columns=cat_dict).sum(axis=1, level=0).reset_index()
temp['year'] = year2
data = data.append(temp)
cols = cat_lookup[['Category']].drop_duplicates()['Category'].tolist()
data['Total'] = data[cols].sum(1)
for item in ['Composition of household']:
    var_dict = fam_code_lookup.loc[fam_code_lookup['Variable'] == item]
    var_dict = dict(zip(var_dict['Category_num'], var_dict['Category_desc']))
    data[item.lower()] = data[item.lower()].map(var_dict)
data.to_csv(wd + 'data/processed/GHG_Estimates_LCFS/Regression_data.csv')
