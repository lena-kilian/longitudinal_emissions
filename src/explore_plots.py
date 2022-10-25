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
    4. emission_summary.py
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import copy as cp

axis = 'tCO$_{2}$e / capita'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':11})

ref_year = 2007

years = list(range(2001, 2021))

vars_ghg = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
            'Private and public road transport', 'Air transport', 
            'Recreation, culture, and clothing', 'Other consumption',
            'Total']

vars_ghg_dict = ['Food and\nDrinks', 'Housing, water\nand waste', 'Electricity, gas,\nliquid and\nsolid fuels', 
                 'Private and\npublic road\ntransport', 'Air transport', 
                 'Recreation,\nculture, and\nclothing', 'Other\nconsumption',
                 'Total']

group_dict = {'hhd_type':'Household Composition', 'age_group_hrp':'Age of HRP', 'gor modified':'Region', 
              'income_group':'Income Decile', 'all':'All'}

# import data
data_ghg = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
data_ghg = data_ghg.loc[(data_ghg['group'] != '0') & (data_ghg['group'] != 'Other')]
data_ghg['group'] = data_ghg['group']\
    .str.replace('all_households', 'All households')
#    .str.replace('Other relative household', 'Other relatives')\
#        .str.replace('Single parent/guardian household', 'Single parent/\nguardian\nhousehold')\
#            .str.replace('Two parent/guardian household', 'Two parent/guardian\nhousehold')\
#                .str.replace(' with', '\nwith').str.replace('adult grand', 'adult\ngrand')

data_allyears = data_ghg.loc[data_ghg['year'] == 'all'] 
data_annual = data_ghg.loc[data_ghg['year'] != 'all'] 
data_annual['year'] = pd.to_datetime(data_annual['year'], format="%Y")

inc_max = data_ghg['pc_income'].max() *1.05

##################################
# Calculate mean change per year #
##################################

data_plot = data_annual.loc[(data_annual['group'] == 'All households') & (data_annual['cpi'] == 'regular')]
sns.barplot(data=data_plot, y='year', x='Total', hue='cpi')

years = list(range(2001, 2021))
# in tCO2e/capita
mean_change = cp.copy(data_annual).set_index(['year', 'group_var', 'group', 'cpi'])[vars_ghg + ['pc_income']]\
    .stack().unstack(level='year')
mean_change.columns = [str(x)[:4] for x in mean_change.columns]
keep = []
for year in years[1:]:
    name = str(year-1) + '-' + str(year)
    keep.append(name)
    mean_change[name] = mean_change[str(year)] - mean_change[str(year-1)]
mean_change = mean_change[keep].mean(axis=1).unstack(level=None)

# in pct of tCO2e
mean_change_pct = cp.copy(data_annual).set_index(['year', 'group_var', 'group', 'cpi'])[vars_ghg + ['pc_income']]\
    .stack().unstack(level='year')
mean_change_pct.columns = [str(x)[:4] for x in mean_change_pct.columns]
keep = []
for year in years[1:]:
    name = str(year-1) + '-' + str(year) 
    keep.append(name)
    mean_change_pct[name] = (mean_change_pct[str(year)] - mean_change_pct[str(year-1)]) / mean_change_pct[str(year)] * 100
mean_change_pct = mean_change_pct[keep].mean(axis=1).unstack(level=None)



############################
# Lineplots all households #
############################

# All households
data_plot = data_annual.loc[data_annual['group'] == 'All households'].set_index(['year', 'cpi'])[vars_ghg[:-1]].stack()\
    .reset_index().rename(columns={'level_2':'Product Category', 0:'ghg'})
    
# Plot
# Linegraph values
for cpi in ['regular', 'with_cpi']:
    temp = data_plot.loc[data_plot['cpi'] == cpi]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category', palette='colorblind')
    ax.set_ylabel(axis); ax.set_xlabel('Year')
    plt.legend(bbox_to_anchor=(1.6, 0.75))
    plt.ylim(0, 4.5)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_' + cpi + '.png', bbox_inches='tight', dpi=300)
    plt.show()
    

temp = cp.copy(data_plot); temp['cpi'] = temp['Prices & Multipliers'] = temp['cpi'].map({'with_cpi':'2007 prices and multipliers', 'regular':'Own year'})
fig, ax = plt.subplots(figsize=(7.5, 4))
sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category', palette='colorblind', style='Prices & Multipliers')
ax.set_ylabel(axis); ax.set_xlabel('Year')
plt.legend(bbox_to_anchor=(1.525, 0.9))
plt.ylim(0, 4.25)
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_both.png', bbox_inches='tight', dpi=300)
plt.show()



check = data_plot.loc[data_plot['Product Category'] == 'Air transport'].set_index(['year', 'cpi', 'Product Category']).unstack(level='cpi')
# Linegraph w/ percentage
data_pct = data_plot.set_index(['year', 'cpi', 'Product Category']).unstack(level=[0])
values_ref_year = data_pct[('ghg', str(ref_year) +'-01-01 00:00:00')]
data_pct = data_pct.apply(lambda x: x/values_ref_year*100).stack().reset_index()

for cpi in ['regular', 'with_cpi']:
    temp = data_pct.loc[data_pct['cpi'] == cpi]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category', palette='colorblind')
    ax.set_ylabel('Percentage of ' + axis + ' compared to ' + str(ref_year)); ax.set_xlabel('Year')
    plt.legend(bbox_to_anchor=(1.6, 0.75))
    plt.axhline(y=100, linestyle=':', color='k', lw=0.5)
    if cpi == 'regular':
        plt.ylim(20,130)
    else:
        plt.ylim(60, 180)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_pct.png',
                bbox_inches='tight', dpi=300)
    plt.show()
    

############################
# Barplots by demographics #
############################

# All Years

# next to each other
data_plot = cp.copy(data_allyears)
for cpi in ['regular', 'with_cpi']:
    for item in data_plot[['group_var']].drop_duplicates()['group_var']:
        temp = data_plot.loc[(data_plot['group_var'] == item) & (data_plot['cpi'] == cpi)].set_index('group')[vars_ghg]\
            .stack().rename(index=dict(zip(vars_ghg, vars_ghg_dict))).reset_index().\
                rename(columns={'level_1':'Product Category', 0:'ghg'})
        fig, ax = plt.subplots(figsize=(7.5, 5))
        sns.barplot(ax=ax, data=temp, x='Product Category', y='ghg', hue='group', palette='colorblind')
        ax.set_ylabel(axis); ax.set_xlabel('')
        plt.xticks(rotation=90)
        plt.legend(bbox_to_anchor=(1, 0.75))
        plt.axvline(x=6.5, linestyle=':', color='k', lw=0.5)
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_HHDs_' + item + '_' + cpi + '.png',
                    bbox_inches='tight', dpi=300)
        plt.show()

# stacked
color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
data_plot = cp.copy(data_allyears)
data_plot['group'] = data_plot['group'].str.replace('\n', ' ')\
    .str.replace('North West and', 'NW &').str.replace('Yorkshire and the Humber', 'Yorkshire & Humber')\
        .str.replace('Single parent/ guardian household', 'Single parent/guardian')\
            .str.replace('Two parent/guardian household', 'Two parents/guardians')
        
for cpi in ['regular', 'with_cpi']:
    for item in data_plot[['group_var']].drop_duplicates()['group_var']:
        temp = data_plot.loc[(data_plot['group_var'] == item) & (data_plot['cpi'] == cpi)].set_index('group')
        income = temp[['pc_income']]
        temp = temp[vars_ghg[:-1]]
        # make subplot
        fig, ax1 = plt.subplots(figsize=(len(temp.index)/3, 5))
        # axis left
        start = [0] * len(temp)
        for i in range(len(temp.columns)):
            prod = temp.columns[i]
            height = temp[prod]
            ax1.bar(bottom=start, height=height, x=temp.index, color=color_list[i])
            start += height
        ax1.set_ylabel(axis)
        ax1.set_ylim(0, 30)
        if item == 'income_group':
            xloc = 1.1
        elif item == 'hhd_type':
            xloc = 1.63
        else:
            xloc = 1.65
        #plt.legend(temp.columns, bbox_to_anchor=(xloc, 1))
        plt.xlabel(group_dict[item])
        plt.xticks(rotation=90)
        # axis right
        ax2 = ax1.twinx()
        ax2.plot(income.index, income['pc_income'], color='k', lw=2, linestyle='--')
        ax2.scatter(income.index, income['pc_income'], color='k')
        ax2.set_ylabel('Income per capita (weekly)')
        ax2.set_ylim(0, inc_max)
        #plt.legend(['Income'], bbox_to_anchor=(1.3, 0.5))
        # modify plot
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_' + item + '_' + cpi + '_allyears.png',
                    bbox_inches='tight', dpi=300)
        plt.show() 
        
# Individual Years
# plots by years
color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
data_plot = cp.copy(data_annual)
for year in years:
    for cpi in ['regular', 'with_cpi']:
        for item in data_plot[['group_var']].drop_duplicates()['group_var'][:-1]:
            temp = data_plot.loc[(data_plot['group_var'] == item) & 
                                 (data_plot['cpi'] == cpi) & 
                                 (data_plot['year'] == str(year) + '-01-01 00:00:00')]\
                .set_index('group')
            income = temp[['pc_income']]
            temp = temp[vars_ghg[:-1]]
            # make subplot
            fig, ax1 = plt.subplots(figsize=(len(temp.index), 5))
            # axis left
            start = [0] * len(temp)
            for i in range(len(temp.columns)):
                prod = temp.columns[i]
                height = temp[prod]
                ax1.bar(bottom=start, height=height, x=temp.index, color=color_list[i])
                start += height
            ax1.set_ylabel(axis)
            ax1.set_ylim(0, 30)
            plt.legend(temp.columns, bbox_to_anchor=(2, 1))
            plt.xlabel(group_dict[item])
            plt.xticks(rotation=90)
            # axis right
            ax2 = ax1.twinx()
            ax2.plot(income.index, income['pc_income'], color='k', lw=2, linestyle='--')
            ax2.scatter(income.index, income['pc_income'], color='k')
            ax2.set_ylabel('Income per capita (weekly)')
            ax2.set_ylim(0, inc_max)
            plt.legend(['Income'], bbox_to_anchor=(1.5, 0.5))
            # modify plot
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_' + item + '_' + cpi + '_' + str(year) +'.png',
                        bbox_inches='tight', dpi=300)
            plt.show()

# plots by group
color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
data_plot = cp.copy(data_annual)
for cpi in ['regular', 'with_cpi']:
    for item in data_plot[['group']].drop_duplicates()['group']:
        temp = data_plot.loc[(data_plot['group'] == item) & 
                             (data_plot['cpi'] == cpi)].set_index('year')
        group_var = temp['group_var'][0]
        income = temp[['pc_income']]
        temp = temp[vars_ghg[:-1]]
        # make subplot
        fig, ax1 = plt.subplots(figsize=(int(len(temp.index)/4), 5))
        # axis left
        start = [0] * len(temp)
        for i in range(len(temp.columns)):
            prod = temp.columns[i]
            height = temp[prod]
            ax1.bar(bottom=start, height=height, x=[str(x)[:4] for x in temp.index], color=color_list[i])
            start += height
        ax1.set_ylabel(axis)
        ax1.set_ylim(0, 30)
        plt.xlabel('Year')
        plt.xticks(rotation=90)
        # axis right
        ax2 = ax1.twinx()
        ax2.plot([str(x)[:4] for x in income.index], income['pc_income'], color='k', lw=2, linestyle='--')
        ax2.scatter([str(x)[:4] for x in income.index], income['pc_income'], color='k')
        ax2.set_ylabel('Income per capita (weekly)')
        ax2.set_ylim(0, inc_max)
        #plt.legend(['Income'], bbox_to_anchor=(1.3, 0.5))
        # modify plot
        plt.title(cpi + ' ' + group_dict[group_var] + '\n\n ' + item.replace('\n', ' '))
        name = item.replace('\n', '_').replace(' ', '_').replace('/', '_')
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_' + group_var + '_'  + name + '_' + cpi +'.png',
                    bbox_inches='tight', dpi=300)
        plt.show()

#############################
# Lineplots by demographics #
#############################


# plots by group
color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
data_plot = cp.copy(data_annual).rename(columns={'year':'Year'}).rename(columns=dict(zip(vars_ghg, vars_ghg_dict)))
data_plot['Group'] = data_plot['group'].str.replace('\n', ' ')
data_plot['Prices & Multipliers'] = data_plot['cpi'].map({'with_cpi':'2007 prices and multiplier', 'regular':'Own year'})
maxmin = data_plot.describe()
for item in data_plot[['group_var']].drop_duplicates()['group_var']:
    temp = data_plot.loc[(data_plot['group_var'] == item)]
    # make subplot
    # axis left
    fig, axs = plt.subplots(nrows=len(vars_ghg), ncols=1, sharex=True, figsize=(2.5, 10))
    for i in range(len(vars_ghg_dict)):
        # make legend
        var = vars_ghg_dict[i]
        if i == 0:
            sns.lineplot(data=temp, x='Year', y=var, hue='Group', style='Prices & Multipliers', 
                         palette='colorblind', legend=True, lw=0.05)
            plt.legend(bbox_to_anchor=(2.5, 5))
            #plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/Lineplots_' + item + '_LEGEND.png',
            #            bbox_inches='tight', dpi=300)
        # make plot
        sns.lineplot(ax=axs[i], data=temp, x='Year', y=var, hue='Group', style='Prices & Multipliers', 
                     palette='colorblind', legend=False, lw=1)
        ymin = maxmin.loc['min', var] * 0.9; ymax = maxmin.loc['max', var] * 1.1
        axs[i].set_ylim(ymin, ymax)
    plt.xticks(rotation=90)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/Lineplots_' + item + '.png',
                bbox_inches='tight', dpi=300)
    plt.show()
    
        
"""

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
"""