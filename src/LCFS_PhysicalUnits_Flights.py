#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

This file creates controls for physical use of flights in the LCFS

@author: Lena Kilian
"""

import pandas as pd


# Flights
lcf_filepath = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/data/raw/LCFS/'

years = list(range(2001, 2019))
lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))



flight_lookup = pd.read_excel(r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/data/processed/LCFS/Controls/Physical Unit Coding.xlsx', sheet_name='Flights')
flight_lookup = flight_lookup.loc[flight_lookup['Variable'] == 'flydest']
flight_lookup['Year'] = flight_lookup['LCF_Year'].astype(str).str[:4].astype(int)

rawhh = {}
for year in years:
    dvhh_file = lcf_filepath + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    rawhh_file = lcf_filepath + lcf_years[year] + '/tab/' + lcf_years[year] + '_rawhh_ukanon.tab'
    rawhh[year] = pd.read_csv(rawhh_file, sep='\t', index_col=0, encoding='latin1'); rawhh[year].columns = rawhh[year].columns.str.lower()

# Extract flydest data and link to weights to estimate number of flights
flight_data = {}; flight_total = {}
for year in years:
    temp = rawhh[year].columns.tolist()
    flights = []; new_cols = []
    for item in temp:
        if 'flydest' in item:
            flights.append(item); new_cols.append('flydest')
    
    flight_data[year] = pd.DataFrame(rawhh[year][flights].unstack().rename(index=dict(zip(flights, new_cols))))\
        .reset_index()
    flight_data[year].columns = ['Variable', 'case', 'Code']
    
    #count number of flights by case
    flight_total[year] = flight_data[year].drop('Variable', axis=1).apply(lambda x: pd.to_numeric(x, errors='coerce'))\
        .dropna(axis=0, how='any').groupby('case').count().rename(columns={'Code':'flight_count'})
    
    # add weights
    temp2 = flight_lookup.loc[flight_lookup['Year'] == year]
    temp2['Code'] = temp2['Code'].astype(str)
    
    temp2 = flight_data[year].merge(temp2, on=['Variable', 'Code'])
    
    temp2 = temp2.groupby(['LCF_Year', 'Year', 'Variable', 'Category', 'case']).sum()\
        .unstack(level='Category').fillna(0).droplevel(axis=1, level=0).reset_index()
    
    flight_data[year] = flight_data[year].drop(['Code', 'Variable'], axis=1)\
        .drop_duplicates().merge(temp2, on='case', how='left')[['case', 'Domestic', 'International']]\
            .set_index('case').join(flight_total[year]).fillna(0)
    
    
# save to file
writer = pd.ExcelWriter(r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/data/processed/LCFS/Controls/flights_2001-2018.xlsx')
for year in years:
    flight_data[year].to_excel(writer, sheet_name=str(year))
writer.save()
    
