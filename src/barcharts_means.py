#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

calculating elasticities -- using 2007 mutipliers and expenditure adjusted to 2007 cpi

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
summary_var = '50%' # 'mean' # 

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
hhd_ghg = {}; pc_ghg = {}; people = {};
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

all_ghg = pd.DataFrame(columns=['year'])
keep = ['weight', pop, 'no people', 'composition of household', 'population', 'income_group', 'age_group', 
        'student_hhld', 'pc_income']
for year in [2007, 2009]:
    temp = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].rename(columns=cat_dict).sum(axis=1, level=0)
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
        ylab = 'Age Range'
    
    # repeat for all households and all adult households
    if item == 'composition of household':
        temp2 = cp.copy(temp)
        temp2[item] = 'All households'
        temp = temp.append(temp2)
    if item == 'age_group':
        temp2 = cp.copy(temp)
        temp2 = temp2.loc[temp2[item] != 'Other']
        temp2[item] = 'All adult households'
        temp = temp.append(temp2)
    
    temp = temp.groupby(['year', item])[products + ['Total_ghg', 'pc_income']].describe().stack(level=0).reset_index()
    temp['se'] = temp['std'] / np.sqrt(temp['count'])
    
    
    # save as df
    temp2 = cp.copy(temp).rename(columns={item:'family_code'})
    temp2['var'] = item
    all_describe = all_describe.append(temp2)
    
    # sort for plot and remove all households
    temp = temp.loc[temp[item] != 'All households']
    if item == 'composition of household':
        temp = temp.sort_values([summary_var, 'year'], ascending=True)
    
    temp = temp.loc[(temp[item] != 'Other') & (temp['level_2'] == 'Total_ghg')]
    
    h = len(temp[[item]].drop_duplicates())
    
    # plot
    fig, ax = plt.subplots(figsize=(8, h/2.5))
    sns.barplot(ax=ax, data=temp, x=summary_var, y=item, hue='year', palette='RdBu',
                edgecolor='black')
    # add errorbars
    x_coords = [p.get_width() for p in ax.patches]
    y_coords = [p.get_y() + 0.5*p.get_height() for p in ax.patches]
    plt.errorbar(x=x_coords, y=y_coords, xerr=temp['se'], fmt="none", c= "k")
    
    # change labens
    plt.ylabel(ylab)
    plt.xlabel('Mean tCO$_{2}$e / capita')
    
    # save
    plt.legend(bbox_to_anchor=(1, 1))
    plt.xlim(0, 30)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barchart_mean_' + item + '_' + summary_var + '.png', bbox_inches='tight', dpi=200)
    plt.show()

# clean up

summary = all_describe[['year', 'var', 'family_code', 'level_2', summary_var]]\
    .drop_duplicates().set_index(['year', 'var', 'family_code', 'level_2'])[[summary_var]]

summary = summary.unstack(['year']).droplevel(axis=1, level=0)
summary[2007] = summary[2007] + 0.000001
summary[2009] = summary[2009] + 0.000001
summary['percentage'] = (summary[2009] - summary[2007]) / summary[2007] * 100
summary = summary.unstack(['level_2'])

order = [(2007, 'pc_income'),
         (2007, 'Total_ghg'),
         (2007, 'Air transport'),
         (2007, 'Electricity, gas, liquid and solid fuels'),
         (2007, 'Food and Drinks'),
         (2007, 'Housing, water and waste'),
         (2007, 'Other consumption'),
         (2007, 'Private and public road transport'),
         (2007, 'Recreation, culture, and clothing'),
         
         ('percentage', 'pc_income'),
         ('percentage', 'Total_ghg'),
         ('percentage', 'Air transport'),
         ('percentage', 'Electricity, gas, liquid and solid fuels'),
         ('percentage', 'Food and Drinks'),
         ('percentage', 'Housing, water and waste'),
         ('percentage', 'Other consumption'),
         ('percentage', 'Private and public road transport'),
         ('percentage', 'Recreation, culture, and clothing')]

summary_final = summary[order].loc[['income_group', 'composition of household', 'age_group']]

"""
products = summary.columns.level[2]
for item in :
"""

final = summary.loc[[('composition of household', 'All households'), ('age_group', 'All adult households')]]\
    .stack(level=1)
    
    
## make stacked barchart:
order = [(2007, 'Air transport'),
         (2007, 'Electricity, gas, liquid and solid fuels'),
         (2007, 'Food and Drinks'),
         (2007, 'Housing, water and waste'),
         (2007, 'Other consumption'),
         (2007, 'Private and public road transport'),
         (2007, 'Recreation, culture, and clothing'),
         (2007, 'Total_ghg'),
             
         (2009, 'Air transport'),
         (2009, 'Electricity, gas, liquid and solid fuels'),
         (2009, 'Food and Drinks'),
         (2009, 'Housing, water and waste'),
         (2009, 'Other consumption'),
         (2009, 'Private and public road transport'),
         (2009, 'Recreation, culture, and clothing'),
         (2009, 'Total_ghg')]

plot_data = summary[order].drop([('composition of household', 'Other'), ('age_group', 'All adult households'), ('age_group', 'Other')])

for year in [2007, 2009]:
    plot_data[year].loc[:,'Air transport':] = plot_data[year].loc[:,'Air transport':].apply(lambda x: x/plot_data[(year, 'Total_ghg')] * 100)
    plot_data = plot_data.drop((year, 'Total_ghg'), axis=1)
    
summary_pct = plot_data.loc[['income_group', 'composition of household', 'age_group']].swaplevel(axis=1).sort_index(1)

hhd_name = ['income_group', 'composition of household', 'age_group']
for i in range(len(hhd_name)):
    item = hhd_name[i]
    temp = plot_data.loc[item].stack(level='year').reset_index()
    temp['group'] = temp['family_code'] + ' ' + temp['year'].astype(str)
    
    h = len(temp[['family_code']].drop_duplicates()) * 2
   
    # plot
    n = len(temp.loc[:,'Air transport':'Recreation, culture, and clothing'].columns)
    custom_palette = sns.color_palette("Paired", n)
    start = [0 for j in range(len(temp.index))]
    for j in range(n):
        var = temp.loc[:,'Air transport':'Recreation, culture, and clothing'].columns[j]
        plt.barh(left=start, width=temp[var], y=temp['group'], color=custom_palette[j])
        start += temp[var]
    
    # change labens
    plt.ylabel(ylab)
    plt.xlabel('Mean tCO$_{2}$e / capita')
    plt.title(summary_var)
    
    # save
    plt.legend(bbox_to_anchor=(1, 1))
    plt.xlim(0, 30)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/stacked_barchart_mean_' + item + '.png', bbox_inches='tight', dpi=200)
    plt.show()