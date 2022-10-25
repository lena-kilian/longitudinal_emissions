#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 2022

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
data_ghg['group'] = data_ghg['group'].str.replace('all_households', 'All households')

data_comp = data_ghg.loc[data_ghg['year'].isin(['2007', '2009', '2019', '2020']) == True]
data_comp['type'] = data_comp['year'].map({'2007':'2007-2009', '2009':'2007-2009', '2019':'2019-2020', '2020':'2019-2020'})
data_comp['year_type'] = data_comp['year'].map({'2007':'First year', '2009':'Last year', '2019':'First year', '2020':'Last year'})
#data_comp['index'] = list(range(len(data_comp)))

data_comp = data_comp.set_index(['type', 'year_type', 'cpi', 'group', 'group_var'])[vars_ghg + ['pc_income']].unstack(level=['type', 'year_type'])\
    .swaplevel(axis=1).swaplevel(axis=1, i=0, j=1).swaplevel(axis=1, i=2, j=1)

for event in ['2007-2009', '2019-2020']:
    for product in vars_ghg + ['pc_income']:
        data_comp[('Difference', event, product)] = data_comp[('Last year', event, product)] - data_comp[('First year', event, product)]
        data_comp[('Percentage difference', event, product)] = data_comp[('Difference', event, product)] / data_comp[('First year', event, product)] * 100
        
data_comp = data_comp.stack().stack().reset_index()

order = ['18-29', '30-49', '50-64', '65-74', '75+', 'Lowest', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', 'Highest', 'All households']
data_comp['group_cat'] = data_comp['group'].astype('category').cat.set_categories(order, ordered=True)

data_comp = data_comp.sort_values('group_cat')

for cpi in ['with_cpi', 'regular']:
    for group in data_comp[['group_var']].drop_duplicates()['group_var']:
        temp = data_comp.loc[(data_comp['cpi'] == cpi) & (data_comp['group_var'] == group)]
        
        pos_x = 2; pos_y = 1;
        fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(3, 5), gridspec_kw={'height_ratios': [8, 1, 1]})
        sns.barplot(ax=axs[0], data=temp.loc[temp['level_3'].isin(['pc_income', 'Total']) == False], x='Difference', y='level_3', ci=None, hue='type', palette='colorblind')
        axs[0].set_xlim(-1, 1); axs[0].axvline(0, c='k', ls='--', lw=0.5); axs[0].set_ylabel('')
        axs[0].legend(bbox_to_anchor=(pos_x, pos_y))
        sns.barplot(ax=axs[1], data=temp.loc[temp['level_3'] == 'Total'], x='Difference', y='level_3', hue='type', palette='colorblind', ci=None)
        axs[1].set_xlim(-2.5, 2.5); axs[1].axvline(0, c='k', ls='--', lw=0.5); axs[1].set_ylabel('')
        axs[1].legend(bbox_to_anchor=(pos_x, pos_y))
        sns.barplot(ax=axs[2], data=temp.loc[temp['level_3'] == 'pc_income'], x='Difference', y='level_3', hue='type', palette='colorblind', ci=None)
        axs[2].set_xlim(-12, 12); axs[2].axvline(0, c='k', ls='--', lw=0.5); axs[2].set_ylabel('')
        axs[2].legend(bbox_to_anchor=(pos_x, pos_y))
        
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lbarplot_difference_' + group + '_' + cpi + '.png', bbox_inches='tight', dpi=300)
        plt.show()
        
        fig, ax = plt.subplots(figsize=(3, 4))
        sns.barplot(ax=ax, data=temp, x='Percentage difference', y='level_3', hue='type', palette='colorblind', ci=None)
        ax.legend(bbox_to_anchor=(pos_x, pos_y))
        ax.set_xlim(-90, 90); ax.axvline(0, c='k', ls='--', lw=0.5);
        
        plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/lbarplot_pct_difference_' + group + '_' + cpi + '.png', bbox_inches='tight', dpi=300)
        plt.show()
        
        
for cpi in ['with_cpi', 'regular']:
    temp = data_comp.loc[(data_comp['cpi'] == cpi) & (data_comp['group_var'] == 'all')]
    
    pos_x = 2; pos_y = 1;
    fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(3, 5), gridspec_kw={'height_ratios': [8, 1, 1]})
    sns.barplot(ax=axs[0], data=temp.loc[temp['level_3'].isin(['pc_income', 'Total']) == False], x='Difference', y='level_3', ci=None, hue='type', palette='colorblind')
    axs[0].set_xlim(-1, 1); axs[0].axvline(0, c='k', ls='--', lw=0.5); axs[0].set_ylabel('')
    axs[0].legend(bbox_to_anchor=(pos_x, pos_y))
    sns.barplot(ax=axs[1], data=temp.loc[temp['level_3'] == 'Total'], x='Difference', y='level_3', hue='type', palette='colorblind', ci=None)
    axs[1].set_xlim(-2.5, 2.5); axs[1].axvline(0, c='k', ls='--', lw=0.5); axs[1].set_ylabel('')
    axs[1].legend(bbox_to_anchor=(pos_x, pos_y))
    sns.barplot(ax=axs[2], data=temp.loc[temp['level_3'] == 'pc_income'], x='Difference', y='level_3', hue='type', palette='colorblind', ci=None)
    axs[2].set_xlim(-12, 12); axs[2].axvline(0, c='k', ls='--', lw=0.5); axs[2].set_ylabel('')
    axs[2].legend(bbox_to_anchor=(pos_x, pos_y))
    
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_difference_all_' + cpi + '.png', bbox_inches='tight', dpi=300)
    plt.show()
    
    fig, ax = plt.subplots(figsize=(3, 4))
    sns.barplot(ax=ax, data=temp, x='Percentage difference', y='level_3', hue='type', palette='colorblind', ci=None)
    ax.legend(bbox_to_anchor=(pos_x, pos_y))
    ax.set_xlim(-90, 90); ax.axvline(0, c='k', ls='--', lw=0.5);
    
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_pct_difference_all_' + cpi + '.png', bbox_inches='tight', dpi=300)
    plt.show()
            
    

for event in ['2007-2009', '2019-2020']:
    for cpi in ['with_cpi', 'regular']:
        for group in data_comp[['group_var']].drop_duplicates()['group_var']:      
            temp = data_comp.loc[(data_comp['cpi'] == cpi) & (data_comp['group_var'] == group) & (data_comp['type'] == event)]
            #l = len(temp[['group']].drop_duplicates()['group'])/2
        
            pos_x = 2; pos_y = 1;
            fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(5, 6), gridspec_kw={'height_ratios': [8, 1, 1]})
            
            temp_data = temp.loc[temp['level_3'].isin(['pc_income', 'Total']) == False]
            sns.barplot(ax=axs[0], data=temp_data, x='Difference', y='level_3', ci=None, hue='group', palette='colorblind')
            x_max = int(max(abs(temp_data['Difference'].min()), temp_data['Difference'].max()) * 1.1 + 1)
            axs[0].set_xlim(-1*x_max, x_max); axs[0].axvline(0, c='k', ls='--', lw=0.5); axs[0].set_ylabel('')
            axs[0].legend(bbox_to_anchor=(pos_x, pos_y))
            
            temp_data = temp.loc[temp['level_3'] == 'Total']
            sns.barplot(ax=axs[1], data=temp_data, x='Difference', y='level_3', hue='group', palette='colorblind', ci=None)
            x_max = int(max(abs(temp_data['Difference'].min()), temp_data['Difference'].max()) * 1.1 + 1)
            axs[1].set_xlim(-1*x_max, x_max); axs[1].axvline(0, c='k', ls='--', lw=0.5); axs[1].set_ylabel('')
            axs[1].legend(bbox_to_anchor=(pos_x, pos_y))
            
            temp_data = temp.loc[temp['level_3'] == 'pc_income']; 
            sns.barplot(ax=axs[2], data=temp_data, x='Difference', y='level_3', hue='group', palette='colorblind', ci=None)
            x_max = int(max(abs(temp_data['Difference'].min()), temp_data['Difference'].max()) * 1.1 + 1)
            axs[2].set_xlim(-1*x_max, x_max); axs[2].axvline(0, c='k', ls='--', lw=0.5); axs[2].set_ylabel('')
            axs[2].legend(bbox_to_anchor=(pos_x, pos_y))
            
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_difference_' + group + '_' + cpi + '_' + event + '.png', bbox_inches='tight', dpi=300)
            plt.show()
            
            
            fig, ax = plt.subplots(figsize=(5, 6))
            sns.barplot(ax=ax, data=temp, x='Percentage difference', y='level_3', hue='group', palette='colorblind', ci=None)
            ax.legend(bbox_to_anchor=(pos_x, pos_y))
            x_max = int((max(abs(temp['Percentage difference'].min()), temp['Percentage difference'].max()) * 1.1 + 1))
            ax.set_xlim(-1*x_max, x_max); ax.axvline(0, c='k', ls='--', lw=0.5);
            
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_pct_difference_' + group + '_' + cpi + '_' + event+ '.png', bbox_inches='tight', dpi=300)
            plt.show() 
            

for event in ['2007-2009', '2019-2020']:
    for cpi in ['with_cpi', 'regular']:
        for group in data_comp[['group_var']].drop_duplicates()['group_var']:      
            temp = data_comp.loc[(data_comp['cpi'] == cpi) & (data_comp['group_var'] == group) & 
                                 (data_comp['type'] == event) & (data_comp['level_3'].isin(['Total', 'pc_income']) == False)]
            l = len(temp[['group']].drop_duplicates()['group'])
            
            fig, ax = plt.subplots(figsize=(5, l))
            sns.barplot(ax=ax, data=temp, x='Difference', y='group', hue='level_3', palette='colorblind', ci=None)
            ax.legend(bbox_to_anchor=(pos_x, pos_y))
            x_max = int((max(abs(temp['Difference'].min()), temp['Difference'].max()) * 1.1 + 1))
            ax.set_xlim(-1*x_max, x_max); ax.axvline(0, c='k', ls='--', lw=0.5);
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_difference_T_' + group + '_' + cpi + '_' + event + '.png', bbox_inches='tight', dpi=300)
            plt.show() 
            
            fig, ax = plt.subplots(figsize=(5, l))
            sns.barplot(ax=ax, data=temp, x='Percentage difference', y='group', hue='level_3', palette='colorblind', ci=None)
            ax.legend(bbox_to_anchor=(pos_x, pos_y))
            x_max = int((max(abs(temp['Percentage difference'].min()), temp['Percentage difference'].max()) * 1.1 + 1))
            ax.set_xlim(-1*x_max, x_max); ax.axvline(0, c='k', ls='--', lw=0.5);
            
            plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/barplot_pct_difference_T_' + group + '_' + cpi + '_' + event+ '.png', bbox_inches='tight', dpi=300)
            plt.show() 