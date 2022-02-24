#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import copy as cp
import estimate_emissions_main_function_2021 as estimate_emissions


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

years = list(range(2001, 2019))

family_name = ['no people', 'People aged <2', 'People aged 2-4', 'People aged 5-15', 'People aged 16-17', 'People aged 18-44', 
               'People aged 45-59', 'People aged 60-64', 'People aged 65-69', 'People aged >69']

# load LFC data
lcfs = {}
people = {}
family_combos = {}

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
    people[year]['no people weighted'] = people[year]['People aged 18-59'] + people[year]['People aged >59'] + (people[year]['People aged <18'] / 2)
    
    for item in family_name[1:]:
        people[year][item + '_total_age'] = people[year][item] * age_dict[item]
    
    people[year]['total age children'] = people[year][['People aged <2_total_age', 'People aged 2-4_total_age', 'People aged 5-15_total_age', 
                                                         'People aged 16-17_total_age']].sum(1)
    people[year]['total age adults'] = people[year][['People aged 18-44_total_age', 'People aged 45-59_total_age', 'People aged 60-64_total_age', 
                                                           'People aged 65-69_total_age', 'People aged >69_total_age']].sum(1)

    # mean ages
    people[year]['mean age children'] = people[year]['total age children'] / people[year]['People aged <18']
    people[year]['mean age adults'] = people[year]['total age adults'] / (people[year]['People aged 18-59'] + people[year]['People aged >59'])
    
    # add household composition information
    people[year] = people[year].reset_index().merge(hhd_comp, how='left', on='type of hhold')
    
    family_combos[year] = people[year][['case', 'hhd_comp_adults', 'hhd_comp_children', 'mean age adults', 'mean age children']]
    family_combos[year]['mean_age_range'] = '18-45'
    family_combos[year].loc[(family_combos[year]['mean age adults'] >= 45) & (family_combos[year]['mean age adults'] < 60), 'mean_age_range'] = '45-60'
    family_combos[year].loc[(family_combos[year]['mean age adults'] >= 60), 'mean_age_range'] = '60+'
    
    family_combos[year] = family_combos[year][['case', 'hhd_comp_adults', 'hhd_comp_children', 'mean_age_range']]
    family_combos[year].loc[(family_combos[year]['hhd_comp_adults'] == '2+ adults') & (family_combos[year]['hhd_comp_children'] == '1+ children'), 'mean_age_range'] = '18-60+'
    family_combos[year].loc[(family_combos[year]['hhd_comp_adults'] == '1 adult') & (family_combos[year]['hhd_comp_children'] == '1+ children'), 'mean_age_range'] = '18-60+'
    family_combos[year].loc[(family_combos[year]['hhd_comp_adults'] == 'Other'), 'mean_age_range'] = 'NA'

    family_combos[year]['hhd_comp'] = family_combos[year]['hhd_comp_adults'] + ' ' + family_combos[year]['mean_age_range'] + ', ' + family_combos[year]['hhd_comp_children']
    family_combos[year] = family_combos[year][['case', 'hhd_comp']]
    
    # Drop unnecessary
    people[year] = people[year][['case', 'weight', 'no people weighted', 'no people']].merge(family_combos[year], how='left', on='case')
    
    # gather spend
    lcfs[year] = lcfs[year].loc[:,'1.1.1.1':'12.5.3.5'].astype(float).apply(lambda x: x*lcfs[year]['weight'])
    
hhd_ghg = estimate_emissions.make_footprint(lcfs, wd)

pc_ghg = {}; hhd_comp_ghg = {}
for year in years:
    hhd_ghg[year] = people[year].join(hhd_ghg[year])
    hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year]['weight'])
    
    pc_ghg[year] = cp.copy(hhd_ghg[year])
    pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'] = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year]['no people weighted'])
    pc_ghg[year]['weighted pop'] = pc_ghg[year]['weight'] * pc_ghg[year]['no people weighted']
    
    count = pc_ghg[year].groupby('hhd_comp').count()[['1.1.1.1']].rename(columns={'1.1.1.1':'count'})
    
    hhd_comp_ghg[year] = hhd_ghg[year].groupby('hhd_comp').sum()
    hhd_comp_ghg[year] = hhd_comp_ghg[year].apply(lambda x: x/hhd_comp_ghg[year]['no people weighted']).loc[:,'1.1.1.1':'12.5.3.5']
    hhd_comp_ghg[year]['count'] = count
    
    print(year, hhd_comp_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1))
    
