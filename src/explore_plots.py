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


pop = 'no people weighted'

if pop == 'no people':
    axis = 'tCO$_{2}$e / capita'
else:
    axis = 'tCO$_{2}$e / adult'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))

fam_code_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/hhd_type_lookup.xlsx')
fam_code_lookup['Category_desc'] = [x.replace('  ', '') for x in fam_code_lookup['Category_desc']]

years = list(range(2001, 2019))

lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))

inflation_070809 = [1, 1.04, 1.03]
# import data
hhd_ghg = {}; pc_ghg = {}; people = {}
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
    people[year] = hhd_ghg[year].loc[:,:'new_desc'].join(income[['hhld_income']])
    people[year]['pc_income'] = people[year]['hhld_income'] / people[year][pop]
    people[year]['population'] = people[year][pop] * people[year]['weight']
    
    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)
    
    people[year]['age_range'] = '18-29'
    for i in [30, 40, 50, 60, 70]:
        people[year].loc[people[year]['age of oldest person in household - anonymised'] > i, 'age_range'] = str(i) + '-' + str(i+9)
    people[year].loc[people[year]['age_range'] == '70-79', 'age_range'] = '70+'
    people[year].loc[people[year]['no people'] != 1, 'age_range'] = 'Other'

#hhd_name = ['new_desc']

hhd_name = ['income_group', 'composition of household', 'age_range']

second_var = None #'number of persons economically active'

if second_var != None:
    data = pd.DataFrame(columns=['case', 'family_code', 'var', 'year', 'CCP1', 'ghg', second_var])
else:
    data = pd.DataFrame(columns=['case', 'family_code', 'var', 'year', 'CCP1', 'ghg'])
    

for item in hhd_name:
    for year in years:
        if second_var != None:
            temp2 = people[year][[item, pop, second_var]].rename(columns={item:'family_code'})
            temp = pc_ghg[year].join(temp2).set_index(['family_code', pop, second_var], append=True).loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
        else:
            temp2 = people[year][[item, pop]].rename(columns={item:'family_code'})
            temp = pc_ghg[year].join(temp2).set_index(['family_code', pop], append=True).loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
        
        temp['Total_ghg'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].sum(axis=1)
        temp = temp.rename(columns=cat_dict)
        temp = temp.sum(axis=1, level=0).stack().reset_index().rename(columns={'level_3':'CCP1', 'level_4':'CCP1', 0:'ghg'})
        temp['year'] = year
        temp['var'] = item
        data = data.append(temp)
        print(year)
    print(item)
  
    
for item in hhd_name:
    temp2 = data.loc[(data['var'] == item) & (data['year'] >= 2007) & (data['year'] <= 2009)]
    product_list = data[['CCP1']].drop_duplicates()['CCP1']
    
    for i in range(len(product_list)):
        product = product_list[i]
        temp = temp2.loc[(temp2['CCP1'] == product)]
        
        if item == 'income_group':
            temp = temp.sort_values('family_code', ascending=False)
            temp['family_code'] = ['Decile ' + str(x+1) for x in temp['family_code']]
        elif item == 'composition of household':
            code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
            code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
            temp['family_code'] = temp['family_code'].map(code_dict)
            temp = temp.sort_values('family_code', ascending=True)
        elif item == 'age_range':
            temp = temp.sort_values('family_code', ascending=True)
        
        temp = temp.loc[temp['family_code'] != 'Other']

        fig, ax = plt.subplots(figsize=(8, 4))
        sns.boxplot(ax=ax, data=temp, hue='year', x='ghg', y='family_code', fliersize=0.75, palette='Blues')
        ax.set_xlabel(axis)
        ax.set_ylabel('Income / adult')
        ax.legend(loc='lower right', title='Year')
        plt.title(product)
        xmax = [10, 8, 6, 3, 25, 20, 10, 60][i]

        plt.xlim(0, xmax)
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/' + item + '_' + product + '.png',
                    bbox_inches='tight', dpi=200)
        plt.show()
    
fig, axs = plt.subplots(ncols=1, nrows=len(hhd_name), figsize=(8, 4*len(hhd_name)), sharex=True)   
for j in range(len(hhd_name)):
    item = hhd_name[j]
    temp2 = data.loc[(data['var'] == item) & (data['year'] >= 2007) & (data['year'] <= 2009)]
    temp = temp2.loc[(temp2['CCP1'] == 'Total_ghg')]

    if item == 'income_group':
        temp = temp.sort_values('family_code', ascending=False)
        temp['family_code'] = ['Decile ' + str(x+1) for x in temp['family_code']]
    elif item == 'composition of household':
        code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
        code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
        temp['family_code'] = temp['family_code'].map(code_dict)
        temp = temp.sort_values('family_code', ascending=True)
    elif item == 'age_range':
        temp = temp.sort_values('family_code', ascending=True)
        
    temp = temp.loc[temp['family_code'] != 'Other']
    
    sns.boxplot(ax=axs[j], data=temp, hue='year', x='ghg', y='family_code', fliersize=0.75, palette='Blues')
    axs[j].set_ylabel(['Income / adult', 'Household Composition', 'Age range (single person household)'][j])
    axs[j].legend(loc='lower right', title='Year')
    axs[j].set_xlabel('')
    
axs[len(hhd_name)-1].set_xlabel(axis)
plt.xlim(0, 60)
plt.subplots_adjust(hspace=0.075)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/ALL_TOTAL.png', bbox_inches='tight', dpi=200)
plt.show()

      

# all households 
temp2 = data.loc[(data['CCP1'] != 'Total_ghg') & (data['year'] >= 2007) & (data['year'] <= 2009)]
med = temp2.groupby(['CCP1']).median()[['ghg']].rename(columns={'ghg':'median'}).reset_index()
temp = temp2.merge(med, on = ['CCP1']).sort_values('median', ascending=False)

fig, ax = plt.subplots(figsize=(7, 5))
sns.boxplot(ax=ax, data=temp, hue='year', x='ghg', y='CCP1', fliersize=0.75, palette='Blues')
ax.set_xlabel(axis)
ax.set_ylabel('')
ax.legend(loc='lower right', title='Year')
plt.title(product)
plt.xlim(0, 30)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/all_households.png', bbox_inches='tight')
plt.show()



# Linegraph
temp = data.loc[(data['CCP1'] != 'Total_ghg')]
temp['ghg'] = temp['ghg'] * temp[pop]
temp = temp.groupby(['year', 'CCP1']).sum().reset_index()
temp['ghg'] = temp['ghg'] / temp[pop]
temp['year'] = pd.to_datetime(temp['year'], format="%Y")
temp = temp.set_index(['year', 'CCP1']).unstack('CCP1')[['ghg']].droplevel(axis=1, level=0)

# Plot
# Linegraph with or without children
item = 'composition of household'
code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
code_dict['new'] = 'Adults only'
code_dict.loc[code_dict['Category_desc'].str.contains('child') == True, 'new'] = 'Adults with children'
code_dict.loc[code_dict['Category_desc'] == 'Other', 'new'] = 'Other'
code_dict = dict(zip(code_dict['Category_num'], code_dict['new']))

temp = data.loc[(data['CCP1'] != 'Total_ghg') & (data['var'] != item)]
temp['family_code'] = temp['family_code'].map(code_dict)
temp['ghg'] = temp['ghg'] * temp[pop]
temp = temp.groupby(['year', 'CCP1', 'family_code']).sum().reset_index()
temp['ghg'] = temp['ghg'] / temp[pop]
temp['year'] = pd.to_datetime(temp['year'], format="%Y")
temp = temp.set_index(['year', 'CCP1', 'family_code']).unstack('CCP1')[['ghg']].droplevel(axis=1, level=0)
temp2 = cp.copy(temp).reset_index()

temp = temp2.loc[temp2['family_code'] != 'Other'].set_index(['year', 'family_code']).stack().reset_index()\
    .rename(columns={0:'ghg', 'family_code':'Household Type', 'CCP1':'Product Category'})

fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category', style='Household Type')
ax.set_ylabel('tCO$_{2}$e / adult'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs.png',
            bbox_inches='tight')
plt.show()


temp5 = temp.set_index(['year', 'Household Type', 'Product Category']).unstack(level=[0])
values_01 = temp5.iloc[:,0]
temp5 = temp5.apply(lambda x: x/values_01*100).stack().reset_index()

fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=temp5, x='year', y='ghg', hue='Product Category', style='Household Type')
ax.set_ylabel('tCO$_{2}$e / adult'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.axhline(y=100, linestyle=':', color='k', lw=0.5)
plt.ylim(50,150)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_pct.png',
            bbox_inches='tight')
plt.show()


temp = data.loc[(data['CCP1'] != 'Total_ghg') & (data['var'] != item)]
temp['family_code'] = 'All'
temp['ghg'] = temp['ghg'] * temp[pop]
temp = temp.groupby(['year', 'CCP1', 'family_code']).sum().reset_index()
temp['ghg'] = temp['ghg'] / temp[pop]
temp['year'] = pd.to_datetime(temp['year'], format="%Y")
temp = temp.set_index(['year', 'CCP1', 'family_code']).unstack('CCP1')[['ghg']].droplevel(axis=1, level=0)
temp2 = cp.copy(temp).reset_index()

temp = temp2.loc[temp2['family_code'] != 'Other'].set_index(['year', 'family_code']).stack().reset_index()\
    .rename(columns={0:'ghg', 'family_code':'Household Type', 'CCP1':'Product Category'})

fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category')
ax.set_ylabel('tCO$_{2}$e / adult'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_all.png',
            bbox_inches='tight')
plt.show()

#temp2.loc[temp2['family_code'] == hhld].drop('family_code', axis=1).set_index('year').plot(kind='bar', stacked=True)



temp = temp2.drop('family_code', axis=1).set_index('year').T
values_01 = temp.iloc[:,0]
temp = temp.apply(lambda x: x/values_01*100).stack().reset_index().rename(columns={0:'ghg', 'CCP1':'Product Category'})
    
fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category')
ax.set_ylabel('Percentage change in tCO$_{2}$e / adult compared to 2001'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.axhline(y=100, linestyle=':', color='k', lw=0.5)
plt.ylim(50,150)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_pct.png', bbox_inches='tight')
plt.show()

 
# get summary statistics
item = 'composition of household'

code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
summary = data.loc[(data['var'] == item) & (data['year'] >= 2007) & (data['year'] <= 2009)]
summary['family_code'] = summary['family_code'].map(code_dict)

temp = cp.copy(summary)
temp['ghg'] = temp['ghg'] * temp[pop]
temp = temp.groupby(['family_code', 'var', 'year', 'CCP1']).sum()
temp[axis] = temp['ghg'] / temp[pop]

summary = summary.groupby(['family_code', 'var', 'year', 'CCP1']).describe()[['ghg']].droplevel(axis=1, level=0).join(temp[[axis]]).droplevel(axis=0, level=1)
summary['IQR'] = summary['75%'] - summary['25%']
summary = summary.unstack(['year'])



# get summary statistics
item = 'composition of household'

income = pd.DataFrame(columns=['family_code', 'year', pop, 'CCP1', 'ghg'])
for year in [2007, 2008, 2009]:
    temp = people[year].reset_index()[[item, pop, 'hhld_income']].reset_index().rename(columns={item:'family_code'})
    temp['ghg'] = temp['hhld_income'] / temp[pop]
    temp['CCP1'] = 'Income'
    temp['year'] = year
    income = income.append(temp)
    income['var'] = item
    
code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
summary = data.loc[(data['var'] == item) & (data['year'] >= 2007) & (data['year'] <= 2009)].append(income[['var','family_code', 'year', 'CCP1', 'ghg', pop]])
summary['family_code'] = summary['family_code'].map(code_dict)

temp = cp.copy(summary)
temp['ghg'] = temp['ghg'] * temp[pop]
temp = temp.groupby(['family_code', 'var', 'year', 'CCP1']).sum()
temp[axis] = temp['ghg'] / temp[pop]

summary = summary.groupby(['family_code', 'var', 'year', 'CCP1']).describe()[['ghg']].droplevel(axis=1, level=0).join(temp[[axis]]).droplevel(axis=0, level=1)
summary['IQR'] = summary['75%'] - summary['25%']
summary = summary.unstack(['year', 'family_code'])[['count', axis]]
