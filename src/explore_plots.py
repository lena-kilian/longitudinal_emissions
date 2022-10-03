#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Plots for all years (2001-2019)

@author: lenakilian
"""

import pandas as pd
import copy as cp
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import LCFS_import_data_function as lcfs_import
import pysal as ps


pop = 'no people'

axis = 'tCO$_{2}$e / capita'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

cat_lookup = pd.read_excel(wd + 'data/processed/LCFS/Meta/lcfs_desc_longitudinal_lookup.xlsx')
cat_lookup['ccp_code'] = [x.split(' ')[0] for x in cat_lookup['ccp']]
cat_dict = dict(zip(cat_lookup['ccp_code'], cat_lookup['Category']))
cat_dict['pc_income'] = 'pc_income'

years = list(range(2001, 2020))

lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020']))

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':11})

# import data
hhd_ghg = {}; pc_ghg = {}; people = {}; hhd_ghg_2007m = {}; pc_ghg_2007m= {}
for year in years:
    file_dvhh = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    file_dvper = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    income = lcfs_import.import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
    income.columns = [x.lower() for x in income.columns]
    income = income[['income anonymised']].rename(columns={'income anonymised':'hhld_income'})
    
    hhd_ghg[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_' + str(year) + '.csv').set_index(['case'])
    pc_ghg[year] = hhd_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/hhd_ghg[year][pop])
    
    people[year] = hhd_ghg[year].loc[:,:'1.1.1.1'].iloc[:,:-1].join(income[['hhld_income']])
    people[year]['pc_income'] = people[year]['hhld_income'] / people[year][pop]
    people[year]['population'] = people[year][pop] * people[year]['weight']
    
    q = ps.Quantiles(people[year]['pc_income'], k=10)
    people[year]['income_group'] = people[year]['pc_income'].map(q)
    
    people[year]['age_group_hrp'] = 'Other'
    for i in [[18, 29], [30, 39], [40, 49], [50, 59], [60, 69], [70, 79]]:
        people[year].loc[people[year]['age hrp'] >= i[0], 'age_group_hrp'] = str(i[0]) + '-' + str(i[1])
    people[year].loc[people[year]['age hrp'] >= 80, 'age_group_hrp'] = '80 or older'
    
    people[year]['gor modified'] = people[year]['gor modified']\
        .map({1:'North East', 2:'North West and Merseyside', 3:'Yorkshire and the Humber', 4:'East Midlands', 5:'West Midlands',
              6:'Eastern', 7:'London', 8:'South East', 9:'South West', 10:'Wales', 11:'Scotland', 12:'Northern Ireland'})
    people[year]['income_group'] = people[year]['income_group']\
        .map(dict(zip(list(range(10)), ['Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])))
        
    people[year]['people aged 17 or younger'] = people[year][['people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17']].sum(1)
    people[year]['people aged 60 or older'] = people[year][['people aged 60-64', 'people aged 65-69', 'people aged >69']].sum(1)     
        

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
# add 2020 data
temp = pd.read_csv(wd + 'temp_2020_results.csv').rename(columns={'cats':'Product Category'})
temp['year'] = 2020
data = data.append(temp)
# clean data
data['year'] = pd.to_datetime(data['year'], format="%Y")
data = data.sort_values('Product Category')
    
# Plot
# Linegraph values
fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=data.reset_index(), x='year', y='ghg', hue='Product Category', palette='colorblind')
ax.set_ylabel(axis); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs.png', bbox_inches='tight', dpi=300)
plt.show()

# Linegraph w/ percentage
data_pct = data.set_index(['year', 'Product Category']).unstack(level=[0])
values_01 = data_pct.iloc[:,0]
data_pct = data_pct.apply(lambda x: x/values_01*100).stack().reset_index()

fig, ax = plt.subplots(figsize=(7.5, 5))
sns.lineplot(ax=ax, data=data_pct, x='year', y='ghg', hue='Product Category', palette='colorblind')
ax.set_ylabel('Percentage of ' + axis + ' compared to 2001'); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.6, 0.75))
plt.axhline(y=100, linestyle=':', color='k', lw=0.5)
plt.ylim(20,130)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_pct.png',
            bbox_inches='tight', dpi=300)
plt.show()


#############################
# Lineplots by demographics #
#############################


data = {}

for item in ['age_group_hrp', 'income_group', 'gor modified']:
    data[item] = pd.DataFrame(columns=['year', item, 'Product Category', axis, pop])
    for year in years:
        temp = pc_ghg[year].loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
        temp = temp.rename(columns=cat_dict).sum(axis=1, level=0).join(people[year][['pc_income', pop, item]])
        temp.loc[:,:'pc_income'] = temp.loc[:,:'pc_income'].apply(lambda x: x*temp[pop])
        temp = temp.groupby(item).sum().set_index([pop], append=True).stack().reset_index().rename(columns={'level_2':'Product Category', 0:axis})
        temp[axis] = temp[axis] / temp[pop]
        temp['year'] = year
        data[item] = data[item].append(temp)
        print(year)
    data[item] = data[item].loc[data[item][item] != 'Other']


# Plot totals
for item in ['age_group_hrp', 'income_group', 'gor modified']:
    total = data[item].loc[data[item]['Product Category'] != 'pc_income'].groupby(['year', item]).sum().reset_index()
    total[item] = total[item].astype(str)
    total['year'] = pd.to_datetime(total['year'], format="%Y")
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sns.lineplot(ax=ax, data=total, x='year', y=axis, hue=item, palette='colorblind')
    ax.set_ylabel(axis); ax.set_xlabel('Year')
    plt.legend(bbox_to_anchor=(1.6, 0.75))
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_totals_' + item +'.png', bbox_inches='tight', dpi=300)
    plt.show()

# Plot product cats
for item in ['age_group_hrp', 'income_group', 'gor modified']:
    cats =  data[item].loc[data[item]['Product Category'] != 'pc_income'].reset_index().drop_duplicates()
    cats['Product Category'] = ['\n' + x for x in cats['Product Category']]
    cats['Year'] = cats['year'].astype(int)
    g = sns.FacetGrid(cats, col='Product Category', hue=item, col_wrap=4, palette='colorblind')
    g.map(sns.lineplot, 'Year', axis)
    plt.legend(bbox_to_anchor=(3.1, 1.5))
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_products_' + item +'.png', bbox_inches='tight', dpi=300)
    plt.show()

# mode: 'economic position of household reference person', 'composition of household', 'category of dwelling', 
#       'ethnicity hrp', 'oac_supergroup', 'type of hhold', 'tenure type', 'ns - sec 8 class of household reference person'
# mean: 'age hrp', pop, 
#       'males aged <2', 'males aged 2-4', 'males aged 5-15', 'males aged 16-17', 'males aged 18-44', 
#       'males aged 45-59', 'males aged 60-64', 'males aged 65-69', 'males aged >69',
#       'females aged <2', 'females aged 2-4', 'females aged 5-15', 'females aged 16-17', 'females aged 18-44', 
#       'females aged 45-59', 'females aged 60-64', 'females aged 65-69', 'females aged >69',
#       'people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17', 'people aged 18-44',
#       'people aged 45-59', 'people aged 60-64', 'people aged 65-69', 'people aged >69',
# weighted mean: ghg emissions, 'pc_income'
    
# get summary stats
summary = pd.DataFrame(columns=[('', 'year')])
for item in ['age_group_hrp', 'income_group', 'gor modified']:
    # weighted mean
    temp_wmean = data[item].rename(columns={item:'group'}).set_index(['group', 'year', 'Product Category'])[[axis]]\
        .unstack(level='Product Category').reset_index().set_index('group').droplevel(axis=1, level=0)
    temp_wmean['Total'] = temp_wmean.loc[:,'Air transport':'Recreation, culture, and clothing'].sum(1)
    temp_wmean.columns = pd.MultiIndex.from_arrays([[''] + (['0_w_mean'] * (len(temp_wmean.columns)-1)), ['year'] + temp_wmean.columns.tolist()[1:]])
    temp_wmean[('', 'var')] = item
    
    temp_mode_all = pd.DataFrame(columns=[('', 'year')])
    temp_mean_all = pd.DataFrame(columns=[('', 'year')])
    for year in years:
        # mode
        temp_mode = cp.copy(people[year])
        temp_mode['group'] = temp_mode[item]
        temp_mode = temp_mode[
            ['group', 'income_group', 'gor modified', 'age_group_hrp', 'economic position of household reference person', 'composition of household', 
             'category of dwelling', 'ethnicity hrp', 'oa class 1d', 'type of hhold', 'tenure type', 
             'ns - sec 8 class of household reference person']]\
            .groupby('group').agg(pd.Series.mode)
        temp_mode.columns = pd.MultiIndex.from_arrays([['2_mode'] * len(temp_mode.columns), temp_mode.columns.tolist()])
        temp_mode[('', 'year')] = year
        temp_mode_all = temp_mode_all.append(temp_mode.reset_index())
        # mean
        temp_mean = cp.copy(people[year])
        temp_mean['group'] = temp_mean[item]
        temp_mean = temp_mean[
            ['group', pop, 'age hrp', 
             #'males aged <2', 'males aged 2-4', 'males aged 5-15', 'males aged 16-17', 'males aged 18-44', 
             #'males aged 45-59', 'males aged 60-64', 'males aged 65-69', 'males aged >69',
             #'females aged <2', 'females aged 2-4', 'females aged 5-15', 'females aged 16-17', 'females aged 18-44', 
             #'females aged 45-59', 'females aged 60-64', 'females aged 65-69', 'females aged >69',
             #'people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17', 'people aged 18-44',
             #'people aged 45-59', 'people aged 60-64', 'people aged 65-69', 'people aged >69'
             'people aged 17 or younger', 'people aged 18-44', 'people aged 45-59', 'people aged 60 or older']]\
            .groupby('group').mean()
        temp_mean.columns = pd.MultiIndex.from_arrays([['1_mean'] * len(temp_mean.columns), temp_mean.columns.tolist()])
        temp_mean[('', 'year')] = year
        temp_mean['0_count', 'hhlds'] = people[year].groupby([item]).count().iloc[:,0]
        temp_mean_all = temp_mean_all.append(temp_mean.reset_index())
        
    
    # fix columns so that tdfs can be merged
    temp_mode_all.columns = pd.MultiIndex.from_tuples(temp_mode_all.columns.tolist()); temp_mode_all = temp_mode_all.set_index([('group', ''), ('', 'year')])
    temp_mean_all.columns = pd.MultiIndex.from_tuples(temp_mean_all.columns.tolist()); temp_mean_all = temp_mean_all.set_index([('group', ''), ('', 'year')])
    temp_all = temp_wmean.reset_index().set_index([('group', ''), ('', 'year')])\
        .join(temp_mode_all).join(temp_mean_all)
        
    summary = summary.append(temp_all.reset_index())
summary.columns = pd.MultiIndex.from_tuples(summary.columns.tolist())
summary = summary.set_index([('group', ''), ('', 'var'), ('', 'year')])



# get summary stats for all years combined
summary_all = pd.DataFrame(columns=[('group', '')])
for item in ['age_group_hrp', 'income_group', 'gor modified']:
    # weighted mean
    temp_wmean = data[item].rename(columns={item:'group'})
    temp_wmean[axis] = temp_wmean[axis]* temp_wmean[pop]
    temp_wmean =  temp_wmean.groupby(['group', 'Product Category']).sum()
    temp_wmean[axis] = temp_wmean[axis]/ temp_wmean[pop]
    temp_wmean = temp_wmean[[axis]].unstack(level='Product Category').reset_index().set_index('group').droplevel(axis=1, level=0)
    temp_wmean['Total'] = temp_wmean.loc[:,'Air transport':'Recreation, culture, and clothing'].sum(1)
    temp_wmean.columns = pd.MultiIndex.from_arrays([[''] + (['0_w_mean'] * (len(temp_wmean.columns)-1)), ['year'] + temp_wmean.columns.tolist()[1:]])
    temp_wmean[('', 'var')] = item
    
    temp_all_years = pd.DataFrame(columns=[''])
    for year in years:
        temp_all_years = temp_all_years.append(cp.copy(people[year]))

    #mode 
    temp_mode = cp.copy(temp_all_years)
    temp_mode['group'] = temp_mode[item]
    temp_mode = temp_mode[
        ['group', 'income_group', 'gor modified', 'age_group_hrp', 'economic position of household reference person', 'composition of household', 
         'category of dwelling', 'ethnicity hrp', 'oa class 1d', 'type of hhold', 'tenure type', 
         'ns - sec 8 class of household reference person']]\
        .groupby('group').agg(pd.Series.mode)
    temp_mode.columns = pd.MultiIndex.from_arrays([['2_mode'] * len(temp_mode.columns), temp_mode.columns.tolist()])
    # mean
    temp_mean = cp.copy(temp_all_years)
    temp_mean['group'] = temp_mean[item]
    temp_mean = temp_mean[
        ['group', pop, 'age hrp', 
         #'males aged <2', 'males aged 2-4', 'males aged 5-15', 'males aged 16-17', 'males aged 18-44', 
         #'males aged 45-59', 'males aged 60-64', 'males aged 65-69', 'males aged >69',
         #'females aged <2', 'females aged 2-4', 'females aged 5-15', 'females aged 16-17', 'females aged 18-44', 
         #'females aged 45-59', 'females aged 60-64', 'females aged 65-69', 'females aged >69',
         #'people aged <2', 'people aged 2-4', 'people aged 5-15', 'people aged 16-17', 'people aged 18-44',
         #'people aged 45-59', 'people aged 60-64', 'people aged 65-69', 'people aged >69'
         'people aged 17 or younger', 'people aged 18-44', 'people aged 45-59', 'people aged 60 or older']]\
        .groupby('group').mean()
    temp_mean.columns = pd.MultiIndex.from_arrays([['1_mean'] * len(temp_mean.columns), temp_mean.columns.tolist()])
    temp_mean['0_count', 'hhlds'] = temp_all_years.groupby([item]).count().iloc[:,-1]
        
    temp_all = temp_wmean.drop([('', 'year')], axis=1).join(temp_mode).join(temp_mean)
        
    summary_all = summary_all.append(temp_all.reset_index())
summary_all.columns = pd.MultiIndex.from_tuples(summary_all.columns.tolist())
summary_all = summary_all.set_index([('group', ''), ('', 'var')])
