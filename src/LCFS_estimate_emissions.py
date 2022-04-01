#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import estimate_emissions_main_function_2021 as estimate_emissions
import pysal as ps


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

hhd_comp_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp_lookup.xlsx')
hhd_comp_dict = dict(zip(hhd_comp_lookup['Code'], hhd_comp_lookup['New Description']))

hhd_comp3_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp3_lookup.xlsx', sheet_name='final')

years = list(range(2001, 2019))

family_name = ['no people', 'People aged <2', 'People aged 2-4', 'People aged 5-15', 'People aged 16-17', 'People aged 18-44', 
               'People aged 45-59', 'People aged 60-64', 'People aged 65-69', 'People aged >69']

k=5 # number of quantiles for income grouping
# load LFC data
lcfs = {}
people = {}
family_combos = {}
hhd_comp3 = {}

comp = {}

age_dict = {'People aged <2':1, 'People aged 2-4':3, 'People aged 5-15':10, 
            'People aged 16-17':17, 'People aged 18-44':31.5, 'People aged 45-59':52.5, 
            'People aged 60-64':62.5, 'People aged 65-69':67.5, 'People aged >69':70}


hhd_comp = pd.read_excel(wd + 'data/processed/LCFS/household_comp_code.xlsx')
hhd_comp.columns = ['a062_desc', 'type of hhold', 'hhd_comp2', 'hhd_comp_adults', 'hhd_comp_children']

for year in years:
    lcfs[year] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv').set_index('case')
    
    # Get household makeup details
    people[year] = lcfs[year].loc[:,:'rooms in accommodation']
    people[year]['People aged <18'] = people[year][['People aged <2', 'People aged 2-4', 'People aged 5-15', 'People aged 16-17']].sum(1)
    people[year]['People aged 18-59'] = people[year][['People aged 18-44', 'People aged 45-59']].sum(1)
    people[year]['People aged >59'] = people[year][['People aged 60-64', 'People aged 65-69', 'People aged >69']].sum(1)
    
    # weigh household size by age so that children count 0.5
    people[year]['no people weighted'] = (people[year]['People aged 18-59'] + people[year]['People aged >59'] +
                                          (people[year][['People aged <2', 'People aged 2-4']].sum(1) * 0.5) +
                                          (people[year][['People aged 5-15']].sum(1) * 0.5) +
                                          (people[year][['People aged 16-17']].sum(1) * 1))
    
    # add household composition information
    people[year] = people[year].reset_index().merge(hhd_comp, how='left', on='type of hhold')

    
    for item in ['income_pc', 'income_pc_w']:
        q = ps.Quantiles(people[year][item], k=k)
        people[year][item] = people[year][item].map(q)
        
    people[year]['hhd_comp_new'] = people[year]['Composition of household'].astype(int).map(hhd_comp_dict)
    
    family_combos[year] = people[year][['case', 'hhd_comp_adults', 'hhd_comp_children', 'mean age adults', 'mean age children']]
    family_combos[year]['mean_age_range'] = '18-45'
    family_combos[year].loc[(family_combos[year]['mean age adults'] >= 45) & (family_combos[year]['mean age adults'] < 60), 'mean_age_range'] = '45-60'
    family_combos[year].loc[(family_combos[year]['mean age adults'] >= 60), 'mean_age_range'] = '60+'
    
    family_combos[year]['hhd_comp'] = family_combos[year]['hhd_comp_adults'] + ' ' + family_combos[year]['mean_age_range'] + ', ' + family_combos[year]['hhd_comp_children']
    family_combos[year] = family_combos[year][['case', 'hhd_comp']]
    
    
    # hhd_comp_3
    hhd_comp3[year] = people[year][['case', 'People aged <2', 'People aged 2-4', 'People aged 5-15', 'People aged 16-17', 'People aged 18-44', 
                                    'People aged 45-59', 'People aged 60-64', 'People aged 65-69', 'People aged >69']]

    hhd_comp3[year]['People aged <18'] = (hhd_comp3[year]['People aged <2'] + hhd_comp3[year]['People aged 2-4'] + 
                                         hhd_comp3[year]['People aged 5-15'] + hhd_comp3[year]['People aged 16-17'])

    for item in ['<18', '18-44', '45-59', '60-64', '65-69', '>69']:
        hhd_comp3[year]['CAT_People aged ' + item] = hhd_comp3[year]['People aged ' + item].astype(str) + ' People aged ' + item
        hhd_comp3[year].loc[(hhd_comp3[year]['People aged ' + item] == 0), 'CAT_People aged ' + item] = ' '
        hhd_comp3[year].loc[(hhd_comp3[year]['People aged ' + item] > 2), 'CAT_People aged ' + item] = '3+ People aged ' + item
    
    hhd_comp3[year] = hhd_comp3[year].merge(hhd_comp3_lookup, how='left', on=hhd_comp3_lookup.columns.tolist()[:6])
    
    # Drop unnecessary
    people[year] = people[year].merge(family_combos[year], how='left', on='case')\
        .merge(hhd_comp3[year][['hhd_comp3', 'case']], how='left', on='case')
    
    # gather spend
    lcfs[year] = lcfs[year].loc[:,'1.1.1.1':'12.5.3.5'].astype(float).apply(lambda x: x*lcfs[year]['weight'])
    
hhd_ghg = estimate_emissions.make_footprint(lcfs, wd)

hhd_comp_list = pd.DataFrame(columns=['hhd_comp3'])
for year in years:
    temp = people[year][['hhd_comp3']]
    hhd_comp_list = hhd_comp_list.append(temp)
hhd_comp_list = hhd_comp_list.reset_index().groupby('hhd_comp3').count().rename(columns={'index':'count'}).reset_index()

hhd_comp3_lookup = hhd_comp3_lookup.merge(hhd_comp_list, on='hhd_comp3')
 

for year in years:
    hhd_ghg[year] = people[year].join(hhd_ghg[year])
    hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year]['weight'])
    name = wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv'
    hhd_ghg[year].reset_index().to_csv(name)
    print(str(year) + ' saved')

    
