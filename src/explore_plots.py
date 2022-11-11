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
import datetime

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

for pc in ['no people', 'hhld_oecd_mod']:
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
        
        temp = data_plot.loc[(data_plot['cpi'] == cpi) & (data_plot['Product Category'] == 'pc_income')]
        temp['Product Category'] = 'Weekly income'
        style = {key:value for key,value in zip(temp['Product Category'].unique(), sns._core.unique_dashes(temp['Product Category'].unique().size+1)[1:])}
        ax2 = ax.twinx()
        sns.lineplot(ax=ax2, data=temp, x='year', y='ghg', hue='Product Category', style='Product Category', 
                     dashes=style, palette=sns.color_palette(['k']))
        ax2.set_ylabel('GBP / capita')
        ax2.legend(bbox_to_anchor=(1.6, 0.25))
        if pc =='no people':
            ax.set_ylim(0, 5.5)
            ax2.set_ylim(0, 375)
        else:
            ax.set_ylim(0, 6.75)
            ax2.set_ylim(0, 675)
        for a in [datetime.datetime(2007, 1, 1), datetime.datetime(2009, 1, 1), datetime.datetime(2019, 1, 1), datetime.datetime(2020, 1, 1)]:
            # [datetime.datetime(2006, 7, 1), datetime.datetime(2009, 7, 1), datetime.datetime(2018, 7, 1), datetime.datetime(2020, 7, 1)]
            plt.axvline(x=a, linestyle='dotted', linewidth=1, color='grey')
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
        
    
    ############################
    # Barplots by demographics #
    ############################
    if pc == 'no people':
        pass
    else:
        # All Years
    
        # stacked
        color_list = ['#226D9C', '#C3881F', '#2A8B6A', '#BA611C', '#C282B5', '#BD926E', '#F2B8E0']
        data_plot = cp.copy(data_allyears)

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
                ax1.set_ylim(0, 32.5)
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
                
                
        for cpi in ['with_cpi', 'regular']:
            temp = data_plot.loc[(data_plot['cpi'] == cpi)]
            temp['group'] = temp['group'].str.replace('all_households', 'All households')
            temp['group_cat'] = temp['group'].astype('category').cat.reorder_categories(
                ['All households', 
                 '18-29', '30-49', '50-64', '65-74', '75+', 
                 'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest'])
            temp = temp.sort_values('group_cat')
            temp['group_cat'] = temp['group_cat'].str.replace('All households', 'All\nhouseholds')
            fig, ax1 = plt.subplots(figsize=(7, 5))
            # axis left
            start = [0] * len(temp)
            for i in range(len(vars_ghg[:-1])):
                prod = vars_ghg[i]
                height = temp[prod]
                ax1.bar(bottom=start, height=height, x=temp['group_cat'], color=color_list[i], edgecolor='k', linewidth=0.5)
                start += height
            ax1.set_ylabel(axis)
            ax1.set_xlabel('')
            for j in [0.5, 5.5]:
                ax1.axvline(x=j, linestyle='--', c='grey')
            #ax1.set_ylim(0, 32.5)
            #plt.legend(temp.columns, bbox_to_anchor=(xloc, 1))
            plt.xlabel(group_dict[item])
            plt.xticks(rotation=90)
            # axis right
            ax2 = ax1.twinx()
            ax2.scatter(temp['group_cat'], temp['pc_income'], color='k')
            ax2.set_ylabel('Income per capita (weekly)')
            ax2.set_ylim(0, inc_max[cpi])
            #plt.legend(['Income'], bbox_to_anchor=(1.3, 0.5))
            # modify plot
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_stacked_HHDs_all_cats_' + cpi + '_all_years_' + pc + '.png',
                        bbox_inches='tight', dpi=300)
            plt.show() 

        
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
                ax1.set_ylim(0, 32.5)
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