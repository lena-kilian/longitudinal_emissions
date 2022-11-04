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

for pc in ['no people', 'hhld_oecd_equ']:
    # import data
    data_ghg = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
    data_ghg = data_ghg.loc[(data_ghg['group'] != '0') & (data_ghg['group'] != 'Other') & (data_ghg['pc'] == pc)]
    data_ghg['group'] = data_ghg['group']\
        .str.replace('all_households', 'All households')
    
    data_allyears = data_ghg.loc[data_ghg['year'] == 'all'] 
    data_annual = data_ghg.loc[data_ghg['year'] != 'all'] 
    data_annual['year'] = pd.to_datetime(data_annual['year'], format="%Y")
    
    inc_max = data_ghg.groupby('cpi').max()['pc_income'] *1.025
    
    ##################################
    # Calculate mean change per year #
    ##################################
    
    data_plot = data_annual.loc[(data_annual['group'] == 'All households') & (data_annual['cpi'] == 'regular')]
    
    """
    sns.barplot(data=data_plot, y='year', x='Total', hue='cpi')
    """
    
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
    data_plot = data_annual.loc[data_annual['group'] == 'All households'].set_index(['year', 'cpi'])[vars_ghg[:-1] + ['pc_income']].stack()\
        .reset_index().rename(columns={'level_2':'Product Category', 0:'ghg'})
        
    # Plot
    # Linegraph values
    for cpi in ['regular', 'with_cpi']:
        temp = data_plot.loc[(data_plot['cpi'] == cpi) & (data_plot['Product Category'] != 'pc_income')]
        fig, ax = plt.subplots(figsize=(7.5, 5))
        sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category', palette='colorblind')
        ax.set_ylabel(axis); ax.set_xlabel('Year')
        ax.legend(bbox_to_anchor=(1.6, 0.75))
        ax.set_ylim(0, 5.5)
        
        temp = data_plot.loc[(data_plot['cpi'] == cpi) & (data_plot['Product Category'] == 'pc_income')]
        temp['Product Category'] = 'Weekly income'
        style = {key:value for key,value in zip(temp['Product Category'].unique(), sns._core.unique_dashes(temp['Product Category'].unique().size+1)[1:])}
        ax2 = ax.twinx()
        sns.lineplot(ax=ax2, data=temp, x='year', y='ghg', hue='Product Category', style='Product Category', 
                     dashes=style, palette=sns.color_palette(['k']))
        ax2.set_ylabel('GBP / capita')
        ax2.legend(bbox_to_anchor=(1.6, 0.25))
        ax2.set_ylim(0, 375)
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_' + cpi + '_' + pc + '.png', bbox_inches='tight', dpi=300)
        plt.show()
    
    temp = cp.copy(data_plot); temp['cpi'] = temp['Prices & Multipliers'] = temp['cpi'].map({'with_cpi':'2007 prices and multipliers', 'regular':'Own year'})
    fig, ax = plt.subplots(figsize=(7.5, 4))
    sns.lineplot(ax=ax, data=temp, x='year', y='ghg', hue='Product Category', palette='colorblind', style='Prices & Multipliers')
    ax.set_ylabel(axis); ax.set_xlabel('Year')
    plt.legend(bbox_to_anchor=(1.525, 0.9))
    plt.ylim(0, 5.5)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_both_' + pc + '.png', bbox_inches='tight', dpi=300)
    plt.show()
    
    
    """
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
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lineplot_HHDs_pct_' + pc + '.png',
                    bbox_inches='tight', dpi=300)
        plt.show()
    """
    
    ############################
    # Barplots by demographics #
    ############################
    
    # All Years
    """
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
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_HHDs_' + item + '_' + cpi + '_' + pc + '.png',
                        bbox_inches='tight', dpi=300)
            plt.show()
    """
    
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
            ax1.set_ylim(0, 35)
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
            ax2.set_ylim(0, inc_max[cpi])
            #plt.legend(['Income'], bbox_to_anchor=(1.3, 0.5))
            # modify plot
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_' + item + '_' + cpi + '_allyears_' + pc + '.png',
                        bbox_inches='tight', dpi=300)
            plt.show() 
            
    # Individual Years
    """
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
                ax1.set_ylim(0, 35)
                plt.legend(temp.columns, bbox_to_anchor=(2, 1))
                plt.xlabel(group_dict[item])
                plt.xticks(rotation=90)
                # axis right
                ax2 = ax1.twinx()
                ax2.plot(income.index, income['pc_income'], color='k', lw=2, linestyle='--')
                ax2.scatter(income.index, income['pc_income'], color='k')
                ax2.set_ylabel('Income per capita (weekly)')
                ax2.set_ylim(0, inc_max[cpi])
                plt.legend(['Income'], bbox_to_anchor=(1.5, 0.5))
                # modify plot
                plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_' + item + '_' + cpi + '_' + str(year) + '_' + pc + '.png',
                            bbox_inches='tight', dpi=300)
                plt.show()
    """
                
    """
    # plots by group
    color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
    data_plot = cp.copy(data_annual)
    for cpi in ['regular', 'with_cpi']:
        for item in ['All households', 'Highest', 'Lowest', '18-29', '75+']:#data_plot[['group']].drop_duplicates()['group']:
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
            ax1.set_ylim(0, 35)
            plt.xlabel('Year')
            plt.xticks(rotation=90)
            # axis right
            ax2 = ax1.twinx()
            ax2.plot([str(x)[:4] for x in income.index], income['pc_income'], color='k', lw=2, linestyle='--')
            ax2.scatter([str(x)[:4] for x in income.index], income['pc_income'], color='k')
            ax2.set_ylabel('Income per capita (weekly)')
            ax2.set_ylim(0, inc_max[cpi])
            #plt.legend(['Income'], bbox_to_anchor=(1.3, 0.5))
            # modify plot
            plt.title(cpi + ' ' + group_dict[group_var] + '\n\n ' + item.replace('\n', ' '))
            name = item.replace('\n', '_').replace(' ', '_').replace('/', '_')
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_' + group_var + '_'  + name + '_' + cpi + '_' + pc + '.png',
                        bbox_inches='tight', dpi=300)
            plt.show()
    """
    
    # plots by group
    color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
    data_plot = data_annual.loc[data_annual['year'].isin(['2007-01-01 00:00:00', '2009-01-01 00:00:00', '2019-01-01 00:00:00', '2020-01-01 00:00:00']) == True]
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
                ax1.bar(bottom=start, height=height, x=[str(x)[:4] for x in temp.index], color=color_list[i], linewidth=0.5, edgecolor='k')
                start += height
            ax1.set_ylabel(axis)
            ax1.set_ylim(0, 35)
            ax1.axvline(1.5, c='k', ls='--', lw=0.5)
            plt.xlabel('Year')
            plt.xticks(rotation=90)
            # axis right
            ax2 = ax1.twinx()
            ax2.scatter([str(x)[:4] for x in income.index], income['pc_income'], color='k')
            ax2.set_ylabel('Income per capita (weekly)')
            ax2.set_ylim(0, inc_max[cpi])
            #plt.legend(['Income'], bbox_to_anchor=(1.3, 0.5))
            # modify plot
            plt.title(item.replace('\n', ' '))
            name = item.replace('\n', '_').replace(' ', '_').replace('/', '_')
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_comp_years_' + group_var + '_'  + name + '_' + cpi + '_' + pc + '.png',
                        bbox_inches='tight', dpi=300)
            plt.show()
            
    # plots by group
    fig, ax1 = plt.subplots(figsize=(int(len(temp.index)/4), 5))
    # axis left
    temp2 = temp.stack().reset_index().rename(columns={'level_1':'Product Category', 0:'ghg'})
    sns.barplot(ax=ax1, data=temp2, x='year', y='ghg', hue='Product Category', palette=sns.color_palette(color_list), edgecolor='k')
    ax1.legend(bbox_to_anchor=(2, 1))
    # axis right
    ax2 = ax1.twinx()
    ax2.scatter([str(x)[:4] for x in income.index], income['pc_income'], color='k')
    ax2.set_ylabel('Income per capita (weekly)')
    ax2.set_ylim(0, inc_max[cpi])
    ax2.legend(['Income'], bbox_to_anchor=(4, 0.5))
    # modify plot
    plt.title('LEGEND ONLY')
    name = item.replace('\n', '_').replace(' ', '_').replace('/', '_')
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_LEGEND_' + pc + '.png',
                bbox_inches='tight', dpi=300)
    plt.show()
    
    """
    #############################
    # Lineplots by demographics #
    #############################
    
    vars_ghg = ['Food and Drinks', 'Housing, water and waste', 'Electricity, gas, liquid and solid fuels', 
                'Private and public road transport', 'Air transport', 
                'Recreation, culture, and clothing', 'Other consumption',
                'Total']
    
    vars_ghg_dict = ['Food and\nDrinks', 'Housing, water\nand waste', 'Electricity, gas,\nliquid and\nsolid fuels', 
                     'Private and\npublic road\ntransport', 'Air transport', 
                     'Recreation,\nculture, and\nclothing', 'Other\nconsumption',
                     'Total']
    
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
            # make plot
            sns.lineplot(ax=axs[i], data=temp, x='Year', y=var, hue='Group', style='Prices & Multipliers', 
                         palette='colorblind', legend=False, lw=1)
            ymin = maxmin.loc['min', var] * 0.9; ymax = maxmin.loc['max', var] * 1.1
            axs[i].set_ylim(ymin, ymax)
        plt.xticks(rotation=90)
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/Lineplots_' + item + '_' + pc + '.png',
                    bbox_inches='tight', dpi=300)
        plt.show()
        
        
    # only lowest and highest income decile   
    # plots by group
    color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
    data_plot = cp.copy(data_annual).rename(columns={'year':'Year'}).rename(columns=dict(zip(vars_ghg, vars_ghg_dict)))
    data_plot['Group'] = data_plot['group'].str.replace('\n', ' ')
    data_plot['Prices & Multipliers'] = data_plot['cpi'].map({'with_cpi':'2007 prices and multiplier', 'regular':'Own year'})
    maxmin = data_plot.describe()
    
    temp = data_plot.loc[data_plot['group'].isin(['Lowest', 'Highest']) == True]
    # make subplot
    # axis left
    fig, axs = plt.subplots(nrows=len(vars_ghg), ncols=1, sharex=True, figsize=(2.5, 10))
    for i in range(len(vars_ghg_dict)):
        # make legend
        var = vars_ghg_dict[i]
        # make plot
        sns.lineplot(ax=axs[i], data=temp, x='Year', y=var, hue='Group', style='Prices & Multipliers', 
                     palette='colorblind', legend=False, lw=1)
        ymin = maxmin.loc['min', var] * 0.9; ymax = maxmin.loc['max', var] * 1.1
        axs[i].set_ylim(ymin, ymax)
    plt.xticks(rotation=90)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/Lineplots_highest_lowest_' + pc + '.png',
                bbox_inches='tight', dpi=300)
    plt.show()
    """