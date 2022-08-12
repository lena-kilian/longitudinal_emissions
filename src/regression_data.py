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

filename = "'Household_emissions_2007_multipliers_' + str(year) + '_wCPI.csv'"
#filename = "'Household_emissions_' + str(year) + '.csv'"

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'

products = cat_lookup[['Category']].drop_duplicates()['Category'].tolist()

fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = [2007, 2009]

lcf_years = dict(zip(years, ['2007', '2009']))

# import cpi data --> uses 2015 as base year, change to 2007
inflation = pd.read_csv(wd + 'data/raw/CPI_longitudinal.csv', index_col=0)\
    .loc[[str(x) for x in years], 'CPI INDEX 00: ALL ITEMS 2015=100']\
        .T.dropna(how='all').astype(float)
inflation = inflation.apply(lambda x: x/inflation[str(years[0])])

# import data
hhd_ghg = {}; people = {}
for year in years:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    
    # income
    income = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    income.columns = [x.lower() for x in income.columns]
    income = income[['income anonymised']].rename(columns={'income anonymised':'hhld_income'})
    # adjust for inflation if CPI used and 2007 m
    if filename.split("'")[-2] == '_wCPI.csv':
        income['hhld_income'] = income['hhld_income'] / inflation[str(year)]
    
    #extract person variables
    temp = pd.read_csv(file_dvper, sep='\t')
    temp.columns = [x.lower() for x in temp.columns]
    
    # marital status
    ms = temp.set_index('case')[['a002', 'a006p']]
    # code 0 if not related to anyone in hhld
    ms['relative_hhld'] = 0
    ms.loc[ms['a002'].isin([0, 1, 9]) == False, 'relative_hhld'] = 1
    # code 0 if not in relationship with anyone in hhld
    ms['partner_hhld'] = 0
    ms.loc[ms['a002'].isin([1]) == True, 'partner_hhld'] = 1
    # aggregate to hhld level
    ms = ms.sum(axis=0, level=0)
    ms.loc[ms['partner_hhld'] > 0, 'partner_hhld'] = 1
    ms.loc[ms['relative_hhld'] > 0, 'relative_hhld'] = 1
    
    # mean age
    age = temp.set_index('case')[['a005p']]
    age['mean_age_adults'] = age.loc[age['a005p'] >= 18].mean(axis=0, level=0)['a005p']
    age['mean_age_children'] = age.loc[age['a005p'] < 18].mean(axis=0, level=0)['a005p']
    age = age.mean(axis=0, level=0).rename(columns = {'a005p':'mean_age'})
    
    # sex
    # adults
    sex = temp[['case', 'a004', 'a005p']]
    temp2 = sex.loc[sex['a005p'] >= 18].groupby(['case', 'a004']).count().unstack(level='a004').fillna(0)\
        .droplevel(axis=1, level=0).rename(columns={1:'No_adult_male', 2:'No_adult_female'})
    temp2['fraction_female_adults'] = temp2['No_adult_female'] / temp2.sum(1)
    sex = sex.join(temp2)
    # children
    temp2 = temp[['case', 'a004', 'a005p']]
    temp2 = temp2.loc[temp2['a005p'] < 18].groupby(['case', 'a004']).count().unstack(level='a004').fillna(0)\
        .droplevel(axis=1, level=0).rename(columns={1:'No_children_male', 2:'No_children_female'})
    temp2['No_children'] = temp2['No_children_male'] + temp2['No_children_female']
    sex = sex.set_index('case').join(temp2)
    # all
    temp2 = sex.groupby(['case', 'a004'])[['a005p']].count().unstack(level='a004').fillna(0)\
        .droplevel(axis=1, level=0).rename(columns={1:'No_male', 2:'No_female'})
    temp2['fraction_female'] = temp2['No_female'] / temp2.sum(1)
    sex = sex.join(temp2).mean(axis=0, level=0).drop(['a004', 'a005p'], axis=1)

    
    # emission data
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/' + eval(filename)).set_index(['case'])
    people[year] = hhd_ghg[year].loc[:,:'1.1.1.1'].iloc[:,:-1]\
        .join(income[['hhld_income']])\
            .join(ms[['relative_hhld', 'partner_hhld']])\
                .join(age)\
                    .join(sex)
    people[year]['pc_income'] = people[year]['hhld_income'] / people[year][pop]
    people[year]['population'] = people[year][pop] * people[year]['weight']
    
    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)
    
    # import age range and student status
    temp = pd.read_csv(wd + 'data/processed/LCFS/Socio-demographic/person_variables_' + str(year) + '.csv').set_index('case')
    people[year] = people[year].join(temp[['age_group']])
        #people[year]['age_group'] = people[year]['age_group'] + ' ' + people[year]['student_hhld'] 

all_ghg = pd.DataFrame(columns=['year'])
keep = ['weight', pop, 'no people', 'population', 'oac_supergroup', 'gor modified', 
        'composition of household', 'age_group', 
        'fraction_female_adults', 'fraction_female', 'No_adult_male', 'No_adult_female', 'No_male', 'No_female',
        'No_children_male', 'No_children_female',
        'mean_age_adults', 'mean_age', 'mean_age_children',
        'socio-ec hrp', 'pc_income', 'partner_hhld', 'relative_hhld',
        'people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17',
        'people aged 18-44', 'people aged 45-59', 'people aged 60-64', 'people aged 65-69', 
        'people aged >69']

for year in years:
    temp = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].rename(columns=cat_dict).sum(axis=1, level=0)
    temp['Total_ghg'] = temp.sum(axis=1)
    temp = people[year][keep].join(temp).reset_index()
    temp['year'] = year
    temp = temp[['case', 'year'] + keep + products + ['Total_ghg']]
    all_ghg = all_ghg.append(temp) 
    
all_ghg['hhld_income'] = all_ghg['pc_income'] * all_ghg['no people']
all_ghg['gor modified'] = [str(int(x)) for x in all_ghg['gor modified']]
all_ghg['oac_supergroup'] = [str(x) for x in all_ghg['oac_supergroup']]
    
# map var descriptions
for item in ['composition of household', 'socio-ec hrp']:
    code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
    code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
    all_ghg[item] = all_ghg[item].map(code_dict)
    
# make dummies
var_list = ['oac_supergroup', 'gor modified', 'composition of household', 'age_group', 'socio-ec hrp']
var_abrv = ['oac', 'gor', 'coh', 'age', 'st']

var_dict = dict(zip(var_list, var_abrv))

for var in var_list:
    temp = all_ghg[[var]].drop_duplicates()[var].tolist()
    abrv = var_dict[var] + '_'
    for item in temp:
        new_var = abrv + item.replace(' ', '').replace('+', 'p')
        all_ghg[new_var] = 0
        all_ghg.loc[all_ghg[var] == item, new_var] = 1
    all_ghg = all_ghg.rename(columns = {var:abrv[:-1]})
    
all_ghg.columns = [x.replace('>', 'p').replace('<', 'm').replace(' ', '_').replace(',', '').replace('-', '_').replace('(', '').replace(')', '')
                   for x in all_ghg.columns]

all_ghg['year_before'] = 1
all_ghg.loc[all_ghg['year'] == 2009, 'year_before'] = 0

all_ghg.to_csv(wd + 'data/processed/Longitudinal_model/model_data_2007-09.csv')

print(all_ghg.columns)

 