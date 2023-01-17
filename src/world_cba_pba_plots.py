#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 2022

"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np

axis = 'tCO$_{2}$e / capita'

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

plt.rcParams.update({'font.family':'Times New Roman', 'font.size':11})

# import data
lookup = pd.read_excel(wd + 'data/processed/country_lookup.xlsx')

data_ghg = pd.read_csv(wd + 'data/raw/national_cba_report_1970_2021.txt', sep='\t')
data_ghg = data_ghg.loc[data_ghg['Record'].isin(['CBA_tCO2perCap', 'PBA_tCO2perCap', 'Population']) == True]
data_ghg = data_ghg.merge(lookup[['Country', 'name', 'country group']], on='Country').drop('Country', axis=1)\
    .set_index(['name', 'Record', 'country group']).unstack(level='Record').dropna(how='all', axis=1)

world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')).drop(['continent'], axis=1).rename(columns={'name':'Country_w'})\
    .merge(lookup, on='Country_w').drop(['Country_w', 'Country'], axis=1).set_index(['name'])


for item in ['CBA', 'PBA']:
    fig, ax = plt.subplots(figsize=(7.5, 5))
    map_cba = world.join(data_ghg[[('2019', item + '_tCO2perCap')]]).rename(columns={('2019', item + '_tCO2perCap'):item})
    map_cba.loc[map_cba[item] == 0, item] = np.nan
    map_cba.plot(ax=ax, column=item, cmap='Blues', scheme='quantiles', k=10, 
                 legend=True, edgecolor='k', linewidth=0.25)
    plt.show()
    
data_cont = data_ghg.swaplevel(axis=1)
for yr in range(1970, 2022):
    data_cont[('CBA_tCO2perCap', str(yr))] = data_cont[('CBA_tCO2perCap', str(yr))] * data_cont[('Population', str(yr))]
    data_cont[('PBA_tCO2perCap', str(yr))] = data_cont[('PBA_tCO2perCap', str(yr))] * data_cont[('Population', str(yr))]
data_cont = data_cont.sum(axis=0, level=1)

data_cont = data_cont.stack(level=1)
data_cont.columns = pd.MultiIndex.from_arrays([['tCO$_{2}$e', 'tCO$_{2}$e', 'pop'], data_cont.columns.tolist()])

data_cont[(axis, 'CBA_tCO2perCap')] = data_cont[('tCO$_{2}$e', 'CBA_tCO2perCap')] / data_cont[('pop', 'Population')]
data_cont[(axis, 'PBA_tCO2perCap')] = data_cont[('tCO$_{2}$e', 'PBA_tCO2perCap')] / data_cont[('pop', 'Population')]
  
data_cont = data_cont.set_index(('pop', 'Population'), append=True).stack(level=1).reset_index().rename(columns={'level_1':'year', 'level_3':'Record'})
data_cont['Year'] = data_cont['year'].astype(int)

data_cont['Record'] = data_cont['Record'].str.replace('CBA_tCO2perCap', 'Consumption-based')\
    .str.replace('PBA_tCO2perCap', 'Production-based')
    
data_cont['Region'] = data_cont['country group'].astype('category')\
    .cat.set_categories(['UK', 'EU', 'China', 'India', 'USA', 'Rest of World'])
    

fig, ax = plt.subplots(figsize=(8, 3))
sns.lineplot(ax=ax, data=data_cont, x='Year', y=axis, hue='Region', style='Record', palette='colorblind')
plt.legend(bbox_to_anchor=(1,1))
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/emissions_timeseries_pc.png', bbox_inches='tight', dpi=300)
plt.show()

fig, ax = plt.subplots(figsize=(8, 3))
sns.lineplot(ax=ax, data=data_cont, x='Year', y='tCO$_{2}$e', hue='Region', style='Record', palette='colorblind')
plt.legend(bbox_to_anchor=(1,1))
plt.savefig(wd + 'Longitudinal_Emissions/outputs/Explore_plots/emissions_timeseries_total.png', bbox_inches='tight', dpi=300)
plt.show()