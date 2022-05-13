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


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

results = pd.read_csv(wd + 'data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')
results['year_str'] = ['Year ' + str(x) for x in results['year']]

for item in ['income_group', 'composition of household', 'age_group', 'student_hhld']:
    fig, ax = plt.subplots(figsize=(7.5, 5))
    # Add household groups
    data = results.loc[(results['group_var'] == item) & (results['group'] != 'All households')].sort_values(['group', 'product', 'year'])
    data['product'] = data['year_str'] + ' ' + data['product']
    if item == 'income_group':
        data['order'] = [int(x.replace('Decile ', '')) for x in data['group']]
        data = data.sort_values(['order', 'product', 'year'])
    sns.scatterplot(ax=ax, data=data, x='product', y='elasticity', style='year_str', hue='group', s=70, palette='Blues')
    # Add all households
    data = results.loc[(results['group_var'] == item) & (results['group'] == 'All households')].sort_values(['group', 'product', 'year'])
    data['product'] = data['year_str'] + ' ' + data['product']
    sns.set_palette(sns.color_palette(['#C54A43'])) # '#78AAC8'
    sns.scatterplot(ax=ax, data=data, x='product', y='elasticity', style='year_str', hue='group', s=70)
    # Add other details
    ax.axhline(0, linestyle='--', c='black', lw=0.5)
    ax.set_ylabel('Income elasticities'); ax.set_xlabel('')
    plt.legend(bbox_to_anchor=(1.3, 1))
    ax.tick_params(axis='x', labelrotation=90)
    #ax.set_ylim(-1.5, 5)
    plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/elasticities_regression_' + item + '.png', bbox_inches='tight')
    plt.show()