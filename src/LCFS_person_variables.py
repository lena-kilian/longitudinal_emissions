#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 2022

Making lookup person variables by household case for each year

@author: lenakilian
"""

import pandas as pd
import copy as cp
import pickle
import pysal as ps
from sys import platform

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'
    
    
hhd_comp_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp_lookup.xlsx')
hhd_comp_dict = dict(zip(hhd_comp_lookup['Code'], hhd_comp_lookup['New Description']))

new_desc_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_comp3_lookup.xlsx', sheet_name='final')
age_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/age_lookup.xlsx').drop_duplicates()
fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = list(range(2001, 2021))

lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020',
                             '2020-2021']))


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

# get variables from 'LCFS_adjusted_' + str(year) + '.csv' data
for year in years:
    lcfs[year] = pd.read_csv(wd + 'data/processed/LCFS/Adjusted_Expenditure/LCFS_adjusted_' + str(year) + '.csv').set_index('case')
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
    
    people[year] = people[year].reset_index().set_index('case').join(temp[['hhd_age_group']])

for year in years:
    print(year)
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
     
    #extract person variables
    temp = pd.read_csv(file_dvper, sep='\t')
    temp.columns = [x.lower() for x in temp.columns]
        
    # marital status
    if 'a006p' in temp.columns:
        ms = temp.set_index('case')[['a002', 'a006p']].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
    else:
        ms = temp.set_index('case')[['a002', 'a006']].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
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
    print('marital status done')
    
    # mean age
    age = temp.set_index('case')[['a005p']].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
    # get descriptive vars
    temp2 = age.reset_index().groupby('case').describe().droplevel(axis=1, level=0).fillna(0)[['mean', 'std', 'min', 'max', '50%']]\
        .rename(columns={'mean':'mean_age_all', '50%':'median_age_all', 'std':'std_age_all', 'min':'min_age', 'max':'max_age'})
    # get age range groups
    temp2['range_age_all'] = temp2['max_age'] - temp2['min_age']
    
    age['mean_age_adults'] = age.loc[age['a005p'] >= 18].mean(axis=0, level=0)['a005p']
    age['median_age_adults'] = age.loc[age['a005p'] >= 18].median(axis=0, level=0)['a005p']
    age['std_age_adults'] = age.loc[age['a005p'] >= 18].std(axis=0, level=0)['a005p'].fillna(0)
    age['mean_age_children'] = age.loc[age['a005p'] < 18].mean(axis=0, level=0)['a005p']
    age['std_age_children'] = age.loc[age['a005p'] < 18].std(axis=0, level=0)['a005p'].fillna(0)
    # clean up and drop duplicates
    age = age[['mean_age_adults', 'median_age_adults', 'std_age_adults', 'mean_age_children', 'std_age_children']].fillna(0).mean(axis=0, level=0)\
        .join(temp2)
    
    # make mean and std age groups
    age['age_group'] = 'Other'
    age.loc[age['min_age'] < 18, 'age_group'] = 'Household with children'
    age.loc[age['min_age'] >= 80, 'age_group'] = '80+'
    for i in [[18, 29], [30, 39], [40, 49], [50, 59], [60, 69], [70, 79]]:
        age.loc[(age['min_age'] >= i[0]) & (age['max_age'] <= i[1]), 'age_group'] = str(i[0]) + '-' + str(i[1])
    
    for p in ['all', 'adults']:
        # group mean and median
        age.loc[age['mean_age_' + p].round(0) < 30, 'mean_age_group_' + p] = '0-29'
        age.loc[age['mean_age_' + p].round(0) >= 80, 'mean_age_group_' + p] = '60+'
        age.loc[age['median_age_' + p].round(0) < 30, 'median_age_group_' + p] = '0-29'
        age.loc[age['median_age_' + p].round(0) >= 80, 'median_age_group_' + p] = '60+'
        for i in [[30, 44], [45, 59]]:
            age.loc[(age['mean_age_' + p].round(0) >= i[0]) & (age['mean_age_' + p].round(0) <= i[1]), 'mean_age_group_' + p] = str(i[0]) + '-' + str(i[1])
            age.loc[(age['median_age_' + p].round(0) >= i[0]) & (age['median_age_' + p].round(0) <= i[1]), 'median_age_group_' + p] = str(i[0]) + '-' + str(i[1])
    
        # group std
        q = ps.Quantiles(age['std_age_' + p], k=5)  
        age['std_age_group_' + p + '_q'] = age['std_age_' + p].map(q)
        age['std_age_group_' + p] = '0-5'
        age.loc[age['std_age_' + p] > 5, 'std_age_group_' + p] = '5-10'
        age.loc[age['std_age_' + p] > 10, 'std_age_group_' + p] = '10+'
        # add desctiptives for adults and children only
    age['with_minors'] = False
    age.loc[age['min_age'] < 18, 'with_minors'] = True
    print('age done')
    #####
    #####
    #####
    #####
    #####
    #####
    ##### HERE
    ##### REMOVE THE ONES THAT HAVE TO FEW!!! GROUP UP!!!
    #####
    #####
    #####
#####
##########
#####
#####
#####
#####
        
    # sex
    # all
    temp2 = temp[['case', 'a004', 'a005p']].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
    temp2 = temp2.groupby(['case', 'a004'])[['a005p']].count().unstack(level='a004').fillna(0)\
        .droplevel(axis=1, level=0).rename(columns={1:'No_male', 2:'No_female'})
    temp2['fraction_female'] = temp2['No_female'] / temp2.sum(1)
    sex = cp.copy(temp2)
    # adults
    temp2 = temp[['case', 'a004', 'a005p']].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
    temp2 = temp2.loc[temp2['a005p'] >= 18].groupby(['case', 'a004']).count().unstack(level='a004').fillna(0)\
        .droplevel(axis=1, level=0).rename(columns={1:'No_adult_male', 2:'No_adult_female'})
    temp2['fraction_female_adults'] = temp2['No_adult_female'] / temp2.sum(1)
    sex = sex.join(temp2)
    # children
    temp2 = temp[['case', 'a004', 'a005p']].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
    temp2 = temp2.loc[temp2['a005p'] < 18].groupby(['case', 'a004']).count().unstack(level='a004').fillna(0)\
        .droplevel(axis=1, level=0).rename(columns={1:'No_children_male', 2:'No_children_female'})
    temp2['No_children'] = temp2['No_children_male'] + temp2['No_children_female']
    sex = sex.join(temp2, how='left').fillna(0)
    print('sex done')
    
    people[year] = people[year].join(ms[['relative_hhld', 'partner_hhld']]).join(age).join(sex).reset_index()

    
pickle.dump(people, open(wd + 'data/processed/LCFS/Meta/person_data.p', "wb" ))