#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import estimate_emissions_main_function_2021 as estimate_emissions
import copy as cp


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

hhd_comp_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp_lookup.xlsx')
hhd_comp_dict = dict(zip(hhd_comp_lookup['Code'], hhd_comp_lookup['New Description']))

new_desc_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp3_lookup.xlsx', sheet_name='final')
age_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/age_lookup.xlsx').drop_duplicates()
fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = list(range(2001, 2019))

family_name = ['no people', 'people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17', 'people aged 18-44', 
               'people aged 45-59', 'people aged 60-64', 'people aged 65-69', 'people aged >69']

k=5 # number of quantiles for income grouping
# load LFC data
lcfs = {}
people = {}
family_combos = {}
new_desc = {}

comp = {}

age_dict = {'people aged <2':1, 'people aged 2-4':3, 'people aged 5-15':10, 
            'people aged 16-17':17, 'people aged 18-44':31.5, 'people aged 45-59':52.5, 
            'people aged 60-64':62.5, 'people aged 65-69':67.5, 'people aged >69':70}


hhd_comp = pd.read_excel(wd + 'data/processed/LCFS/household_comp_code.xlsx')
hhd_comp.columns = ['a062_desc', 'type of hhold', 'hhd_comp2', 'hhd_comp_adults', 'hhd_comp_children']


for year in years + ['2007_cpi', '2009_cpi']:
    if year in years:
        lcfs[year] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv').set_index('case')
    else:
        temp = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + year[:4] + '_wCPI.csv').set_index('case')
        lcfs[year] = lcfs[int(year[:4])].loc[:,:'1.1.1.1'].iloc[:,:-1].join(temp.loc[:,'1.1.1.1':'12.5.3.5'])

for year in years + ['2007_cpi', '2009_cpi']:
    # Get household makeup details
    people[year] = lcfs[year].loc[:,:'rooms in accommodation']
    people[year]['people aged <18'] = people[year][['people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17']].sum(1)
    people[year]['people aged 18-59'] = people[year][['people aged 18-44', 'people aged 45-59']].sum(1)
    people[year]['people aged >59'] = people[year][['people aged 60-64', 'people aged 65-69', 'people aged >69']].sum(1)
    
    # weigh household size by age so that children count 0.5
    people[year]['no people weighted'] = people[year]['no people'] - (people[year]['people aged <18'] * 0.25)
    
    # add household composition information
    people[year] = people[year].reset_index().merge(hhd_comp, how='left', on='type of hhold')
        
    people[year]['hhd_comp_new'] = people[year]['composition of household'].astype(int).map(hhd_comp_dict)

    # hhd_comp_3
    new_desc[year] = people[year][['case', 'people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17', 'people aged 18-44', 
                                    'people aged 45-59', 'people aged 60-64', 'people aged 65-69', 'people aged >69']]

    new_desc[year]['people aged <18'] = (new_desc[year]['people aged <2'] + new_desc[year]['people aged 2-4'] + 
                                         new_desc[year]['people aged 5-15'] + new_desc[year]['people aged 16-17'])

    for item in ['<18', '18-44', '45-59', '60-64', '65-69', '>69']:
        new_desc[year]['cat_people aged ' + item] = new_desc[year]['people aged ' + item].astype(str) + ' people aged ' + item
        new_desc[year].loc[(new_desc[year]['people aged ' + item] == 0), 'cat_people aged ' + item] = ' '
        new_desc[year].loc[(new_desc[year]['people aged ' + item] > 2), 'cat_people aged ' + item] = '3+ people aged ' + item
    
    new_desc_lookup.columns = [x.lower() for x in new_desc_lookup.columns.tolist()]
    merge_cols = new_desc_lookup.columns.tolist()[:6]
    new_desc_lookup[merge_cols] = new_desc_lookup[merge_cols].apply(lambda x: x.str.lower())
    new_desc[year] = new_desc[year][['case'] + merge_cols].merge(new_desc_lookup, how='left', on=merge_cols)
    
    # Drop unnecessary
    people[year] = people[year].merge(new_desc[year][['new_desc', 'case']], how='left', on='case')
    
    # add other household types
    # pensioner housheolds
    people[year].loc[(people[year]['type of household'] == 1) & 
                     (people[year]['no people'] == 1), 'composition of household'] = 101
    people[year].loc[(people[year]['type of household'] == 1) & 
                     (people[year]['no people'] > 1), 'composition of household'] = 102
    # young adult households
    people[year].loc[(people[year]['new_desc'] == '1 adult (18-44)') & 
                     (people[year]['age of oldest person in household - anonymised'] < 30), 'composition of household'] = 201
    people[year].loc[(people[year]['new_desc'] == '2 adults (18-44)') & 
                     (people[year]['age of oldest person in household - anonymised'] < 30), 'composition of household'] = 202
    people[year].loc[(people[year]['new_desc'] == '3+ adults (18-44)') & 
                     (people[year]['age of oldest person in household - anonymised'] < 30), 'composition of household'] = 203
    
    # OECD household equivalent scales
    # https://www.oecd.org/economy/growth/OECD-Note-EquivalenceScales.pdf
    temp = cp.copy(people[year])
    temp['<16'] =  temp['people aged <18'] - temp['people aged 16-17']
    temp['16+'] = temp['no people'] - temp['<16']
    temp['hhld_oecd_mod'] = 0
    temp.loc[temp['16+'] > 0, 'hhld_oecd_mod'] = 1
    temp['hhld_oecd_equ'] = temp['hhld_oecd_mod']
    # OECD-modified scale
    temp['hhld_oecd_mod'] = temp['hhld_oecd_mod'] + ((temp['16+'] - 1) * 0.5) + (temp['<16'] * 0.3)
    people[year] = people[year].merge(temp[['hhld_oecd_mod', 'case']], on='case')
    # OECD equivalence scale
    temp['hhld_oecd_equ'] = temp['hhld_oecd_equ'] + ((temp['16+'] - 1) * 0.7) + (temp['<16'] * 0.5)
    people[year] = people[year].merge(temp[['hhld_oecd_equ', 'case']], on='case')
    
    keep = ['age of oldest person in household - anonymised', 'age of household reference person by range - anonymised',  
            'people aged <18', 'people aged 18-44', 'people aged 45-59', 'people aged 60-64', 'people aged 65-69', 'people aged >69']
    temp = people[year].reset_index()[keep + ['case']]
    code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == 'age of household reference person by range - anonymised']
    code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
    temp['age of household reference person by range - anonymised'] = temp['age of household reference person by range - anonymised'].map(code_dict)
    
    temp = temp.merge(age_code_lookup, on=keep, how='left').reset_index().drop_duplicates().rename(columns={'Code':'hhd_age_group'}).set_index('case')
    
    people[year] = people[year].reset_index().set_index('case').join(temp[['hhd_age_group']]).reset_index()
    
    # gather spend      
    lcfs[year] = lcfs[year].loc[:,'1.1.1.1':'12.5.3.5'].astype(float).apply(lambda x: x*lcfs[year]['weight'])

hhd_ghg, multipliers = estimate_emissions.make_footprint({x:lcfs[x] for x in years}, wd)

# household composition
hhd_comp_list = pd.DataFrame(columns=['new_desc'])
for year in years:
    temp = people[year][['new_desc']]
    hhd_comp_list = hhd_comp_list.append(temp)
hhd_comp_list = hhd_comp_list.reset_index().groupby('new_desc').count().rename(columns={'index':'count'}).reset_index()

new_desc_lookup = new_desc_lookup.merge(hhd_comp_list, on='new_desc')
 
# save emissions using their own year multipliers
for year in years:
    hhd_ghg[year] = people[year].set_index('case').join(hhd_ghg[year])
    hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year]['weight'])
    name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv'
    hhd_ghg[year].reset_index().to_csv(name)
    print(str(year) + ' saved')
    
# save emissions using 2007 multipliers
for item in ['2007_cpi', '2009_cpi']:
    year = int(item[:4])
    temp = lcfs[item].T.join(multipliers[year][['multipliers']])
    temp = temp.apply(lambda x: x*temp['multipliers']).drop(['multipliers'], axis=1).T.reset_index().rename(columns={'index':'case'})
    temp = people[year].merge(temp, on='case')
    temp.loc[:,'1.1.1.1':'12.5.3.5'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/temp['weight'])
    name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2007_multipliers_' + str(year) + '_wCPI.csv'
    temp.to_csv(name)
    print(item + ' with 2007 multipliers saved')

    
