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

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'

products = cat_lookup[['Category']].drop_duplicates()['Category'].tolist()

fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = list(range(2001, 2019))

lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))

inflation_070809 = [1, 1.04, 1.03]
# import data
hhd_ghg = {}; pc_ghg = {}; people = {}; hhd_ghg_2007m = {}; pc_ghg_2007m= {}
for year in years:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    income = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    income.columns = [x.lower() for x in income.columns]
    if year >= 2007 and year <= 2009:
        income['income anonymised'] = income['income anonymised'] / inflation_070809[year-2007]
    income = income[['income anonymised']].rename(columns={'income anonymised':'hhld_income'})
    
    
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv').set_index(['case'])
    pc_ghg[year] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year][pop])
    people[year] = hhd_ghg[year].loc[:,:'1.1.1.1'].iloc[:,:-1].join(income[['hhld_income']])
    people[year]['pc_income'] = people[year]['hhld_income'] / people[year][pop]
    people[year]['population'] = people[year][pop] * people[year]['weight']
    
    if year in [2007, 2008, 2009]:
        hhd_ghg_2007m[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_2007_multipliers_' + str(year) + '.csv')\
            .set_index('case')
        pc_ghg_2007m[year] = hhd_ghg_2007m[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg_2007m[year][pop])
    
    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)
    
    # import age range and student status
    if year in [2007, 2008, 2009]:
        temp = pd.read_csv(wd + 'data/processed/LCFS/Socio-demographic/person_variables_' + str(year) + '.csv').set_index('case')
        people[year] = people[year].join(temp[['age_group', 'student_hhld']])
        #people[year]['age_group'] = people[year]['age_group'] + ' ' + people[year]['student_hhld'] 

all_ghg = pd.DataFrame(columns=['year'])
keep = ['weight', pop, 'no people', 'composition of household', 'population', 'income_group', 'age_group', 
        'student_hhld', 'pc_income']
for year in [2007, 2009]:
    temp = pc_ghg_2007m[year].loc[:,'1.1.1.1':'12.5.3.5'].rename(columns=cat_dict).sum(axis=1, level=0)
    temp['Total_ghg'] = temp.sum(axis=1)
    temp = people[year][keep].join(temp).reset_index()
    temp['year'] = year
    temp = temp[['case', 'year'] + keep + products + ['Total_ghg']]
    all_ghg = all_ghg.append(temp) 
    
# expand data
weight = 'weight'

def reindex_df(df, weight_col):
    """expand the dataframe to prepare for resampling
    result is 1 row per count per sample"""
    df = df.reindex(df.index.repeat(df[weight_col]))
    df.reset_index(drop=True, inplace=True)
    return(df)

df = all_ghg.loc[:,:'student_hhld'].reset_index()
df['rep_weight'] = [int(round(x)) for x in df[weight]]

df = reindex_df(df[['year', 'case', 'rep_weight']], weight_col = 'rep_weight')

all_data = df.merge(all_ghg, on=['year', 'case'])
all_data.index = list(range(len(all_data)))


all_describe = pd.DataFrame(columns=['year'])
hhd_name = ['income_group', 'composition of household', 'age_group']
for i in range(len(hhd_name)):
    item = hhd_name[i]
    temp = cp.copy(all_data)
    if item == 'income_group':
        temp = temp.sort_values([item, 'year'], ascending=False)
        temp[item] = ['   ' + str((int(x))) + '       Decile ' + str((int(x+1))) for x in temp[item]]
        temp[item] = temp[item].str.replace('Decile 10', 'Highest').str.replace('Decile 1', 'Lowest')
        ylab = 'Income Decile'
    elif item == 'composition of household':
        code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
        code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
        temp[item] = temp[item].map(code_dict)
        ylab = 'Housheold Composition'
    elif item == 'age_group':
        temp = temp.sort_values([item, 'year'], ascending=True)
        temp = temp.loc[temp[item] != 'Household with children']
        ylab = 'Age Range\n(Adult Households Only)'
    
    temp = temp.groupby(['year', item])[products + ['Total_ghg', 'pc_income']].describe().stack(level=0).reset_index()
    temp['se'] = temp['std'] / np.sqrt(temp['count'])
    all_describe = all_describe.append(temp)
    
    if item == 'composition of household':
        temp = temp.sort_values(['mean', 'year'], ascending=True)
    
    temp = temp.loc[(temp[item] != 'Other') & (temp['level_2'] == 'Total_ghg')]
    
    h = len(temp[[item]].drop_duplicates())
    
    fig, ax = plt.subplots(figsize=(8, h/2.5))
    sns.barplot(ax=ax, data=temp, x='mean', y=item, hue='year', palette='RdBu',
                edgecolor='black')
    x_coords = [p.get_width() for p in ax.patches]
    y_coords = [p.get_y() + 0.5*p.get_height() for p in ax.patches]
    plt.errorbar(x=x_coords, y=y_coords, xerr=temp['se'], fmt="none", c= "k")
    
    plt.ylabel(ylab)
    plt.xlabel('Mean tCO$_{2}$e / capita')
    
    plt.legend(bbox_to_anchor=(1, 1))
    plt.xlim(0, 30)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barchart_mean_' + item + '.png', bbox_inches='tight', dpi=200)
    plt.show()

    
