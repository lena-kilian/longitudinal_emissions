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
from sys import platform

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

axis_og = 'tCO$_{2}$e / '


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
    if pc == 'no people':
        axis = axis_og + 'capita'
    else:
        axis = axis_og + 'SPH'
    # import data
    data_ghg = pd.read_csv(wd + 'Longitudinal_Emissions/outputs/Summary_Tables/weighted_means_and_counts.csv')
    data_ghg = data_ghg.loc[(data_ghg['group'] != '0') & (data_ghg['group'] != 'Other') & (data_ghg['pc'] == pc)]
    data_ghg['group'] = data_ghg['group']\
        .str.replace('all_households', 'All households')
    
    data_allyears = data_ghg.loc[data_ghg['year'] == 'all'] 
    data_annual = data_ghg.loc[data_ghg['year'] != 'all'] 
    data_annual['year'] = pd.to_datetime(data_annual['year'], format="%Y")
    
    check = data_ghg.loc[data_ghg['year'] == '2020']
    
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
        #style = {key:value for key,value in zip(temp['Product Category'].unique(), sns._core.unique_dashes(temp['Product Category'].unique().size+1)[1:])}
        ax2 = ax.twinx()
        sns.lineplot(ax=ax2, data=temp, x='year', y='ghg', hue='Product Category', style='Product Category', # dashes=style, 
                     palette=sns.color_palette(['k']))
        ax2.set_ylabel('GBP / SPH')
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