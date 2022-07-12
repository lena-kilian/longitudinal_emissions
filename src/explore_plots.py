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


# save results for regression
year1 = 2007; year2 = 2009
data = people[year1].reset_index().merge(pc_ghg_2007m[year1].rename(columns=cat_dict).sum(axis=1, level=0).reset_index(), on='case')
data['year'] = year1
temp = people[year2].reset_index().merge(pc_ghg_2007m[year2].rename(columns=cat_dict).sum(axis=1, level=0).reset_index(), on='case')
temp['year'] = year2
data = data.append(temp)
cols = cat_lookup[['Category']].drop_duplicates()['Category'].tolist()
data['Total'] = data[cols].sum(1)
for item in ['Composition of household']:
    var_dict = fam_code_lookup.loc[fam_code_lookup['Variable'] == item]
    var_dict = dict(zip(var_dict['Category_num'], var_dict['Category_desc']))
    data[item.lower()] = data[item.lower()].map(var_dict)
data['income_group'] = ['Decile ' + str(x+1) for x in data['income_group']]
data.to_csv(wd + 'data/processed/GHG_Estimates_LCFS/Regression_data.csv')

#######################
# Lineplots all years #
#######################


data = pd.DataFrame(columns=['year', 'Product Category', 'ghg'])
    
for year in years:
    temp = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
    temp = temp.rename(columns=cat_dict).sum(axis=1, level=0).join(people[year][[pop]])
    temp.loc[:,:'Air transport'] = temp.loc[:,:'Air transport'].apply(lambda x: x*temp[pop])
    temp = pd.DataFrame(temp.sum(0)).reset_index().rename(columns={'index':'Product Category', 0:'ghg'})
    temp['ghg'] = temp['ghg'] / temp.iloc[-1, -1]
    temp = temp.loc[temp['Product Category'] != pop]
    temp['year'] = year
    data = data.append(temp)
    print(year)
data['year'] = pd.to_datetime(data['year'], format="%Y")
    
# Plot
# Linegraph values
fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=data.reset_index(), x='year', y='ghg', hue='Product Category')
ax.set_ylabel('tCO$_{2}$e / adult'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs.png', bbox_inches='tight')
plt.show()

# Linegraph w/ percentage
data_pct = data.set_index(['year', 'Product Category']).unstack(level=[0])
values_01 = data_pct.iloc[:,0]
data_pct = data_pct.apply(lambda x: x/values_01*100).stack().reset_index()

fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=data_pct, x='year', y='ghg', hue='Product Category')
ax.set_ylabel('tCO$_{2}$e / adult'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.axhline(y=100, linestyle=':', color='k', lw=0.5)
plt.ylim(50,150)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_pct.png',
            bbox_inches='tight')
plt.show()

######################
# Boxplots 2007-2009 #
######################

hhd_name = ['income_group', 'composition of household', 'age_group']

data = pd.DataFrame(columns=['case', 'family_code', 'var', 'year', 'CCP1', 'ghg'])    
 
for item in hhd_name:
     for year in [2007, 2008, 2009]:
         temp2 = people[year][[item, pop, 'pc_income']].rename(columns={item:'family_code'})
         temp = pc_ghg_2007m[year].loc[:,'1.1.1.1':'12.5.3.5'].join(temp2)\
             .set_index(['family_code', pop], append=True).dropna(how='all')
         temp['Total_ghg'] = temp.loc[:,'1.1.1.1':'12.5.3.5'].sum(axis=1)
         temp = temp.rename(columns=cat_dict)
         temp = temp.sum(axis=1, level=0).stack().reset_index().rename(columns={'level_3':'CCP1', 'level_4':'CCP1', 0:'ghg'})
         temp['year'] = year
         temp['var'] = item
         data = data.append(temp)
         print(year)
     print(item)
   
data_all = cp.copy(data)
data = data.loc[data['CCP1']!='pc_income']
     
for item in hhd_name:
     temp2 = data.loc[(data['var'] == item) & (data['year'] >= 2007) & (data['year'] <= 2009)]
     product_list = data[['CCP1']].drop_duplicates()['CCP1']
     
     for i in range(len(product_list)):
         product = product_list.tolist()[i]
         temp = temp2.loc[(temp2['CCP1'] == product)]
         
         if item == 'income_group':
             temp = temp.sort_values('family_code', ascending=False)
             temp['family_code'] = ['Decile ' + str(x+1) for x in temp['family_code']]
         elif item == 'composition of household':
             code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == item]
             code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
             temp['family_code'] = temp['family_code'].map(code_dict)
             temp = temp.sort_values('family_code', ascending=True)
         else:
             temp = temp.sort_values('family_code', ascending=True)
             temp = temp.loc[temp['family_code'] != 'Household with children']
         
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
    elif item == 'age_group':
        temp = temp.sort_values('family_code', ascending=True)
        temp = temp.loc[temp['family_code'] != 'Household with children']
        
    temp = temp.loc[temp['family_code'] != 'Other']
    
    sns.boxplot(ax=axs[j], data=temp, hue='year', x='ghg', y='family_code', fliersize=0.75, palette='Blues')
    axs[j].set_ylabel(['Income / adult', 'Household Composition', 'Age range', 'All student household'][j])
    axs[j].legend(loc='lower right', title='Year')
    axs[j].set_xlabel('')
    
axs[len(hhd_name)-1].set_xlabel(axis)
plt.xlim(0, 60)
plt.subplots_adjust(hspace=0.075)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/ALL_TOTAL.png', bbox_inches='tight', dpi=200)
plt.show()


# make summary 
summary = data_all.loc[(data_all['year'] != 2008) & (data_all['var'] != 'student_hhld')]

# add all households
temp = summary.loc[summary['var'] == 'composition of household']
temp['var'] = 'All households'
temp['family_code'] = 'All households'

summary = summary.append(temp)
summary.index = list(range(len(summary)))

# replace numeric categories
code_dict = fam_code_lookup.loc[fam_code_lookup['Variable'].str.lower() == 'composition of household']
code_dict = dict(zip(code_dict['Category_num'], code_dict['Category_desc']))
summary.loc[summary['var'] == 'composition of household', 'family_code'] = summary['family_code'].map(code_dict)
summary.loc[summary['var'] == 'income_group', 'family_code'] = 'Decile ' + summary['family_code'].astype(str)

# get means
summary['ghg'] = summary['ghg'] * summary[pop]
summary = summary.groupby(['var', 'year', 'CCP1', 'family_code']).sum()
summary['ghg'] = summary['ghg'] / summary[pop]
summary = summary[['ghg']].unstack(level='year').droplevel(axis=1, level=0)
summary[2007] = summary[2007] + 0.000001
summary[2009] = summary[2009] + 0.000001
summary['percentage'] = (summary[2009] - summary[2007]) / summary[2007] * 100
summary = summary.drop(2009, axis=1).unstack(level='CCP1').reset_index()

