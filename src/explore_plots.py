#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Plots for all years (2001-2019)

@author: lenakilian

Before this run:
    1. LCFS_import_data_function.py
    2. LCFS_import_data.py
    3. LCFS_estimate_emissions.py
    4. expand_to_UK_pop.py
"""

import pandas as pd
import copy as cp
import seaborn as sns
import matplotlib.pyplot as plt
import pickle




#[['case', 'hhld_oecd_equ', 'hhld_oecd_mod', 'no people', 'no people <18', 'no_adults',
#     'hhd_type', 'pc_income', 'income_group', 'income anomymised', 'age_hrp', 'age_group_hrp', 'rooms in accommodation']]

axis = 'tCO$_{2}$e / capita'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':11})

years = list(range(2001, 2020))

# import data
hhd_ghg_uk = pickle.load(open(wd + 'data/processed/GHG_Estimates_LCFS/Household_emissions_population.p', 'rb'))


#######################
# Lineplots all years #
#######################


data = pd.DataFrame(columns=['year', 'Product Category', 'ghg'])
    
for year in years:
    temp = hhd_ghg_uk[year].loc[:,'1.1.1.1':'12.5.3.5'].dropna(how='all')
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
