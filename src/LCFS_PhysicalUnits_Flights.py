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

years = list(range(2001, 2020))
lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020']))



flight_lookup = pd.read_excel(r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/data/processed/LCFS/Controls/Physical Unit Coding.xlsx', sheet_name='Flights')
flight_lookup = flight_lookup.loc[flight_lookup['Variable'] == 'flydest']
flight_lookup['Year'] = flight_lookup['LCF_Year'].astype(str).str[:4].astype(int)

rawhh = {}; dvhh = {}
for year in years:
    dvhh_file = lcf_filepath + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvhh_ukanon.tab'
    rawhh_file = lcf_filepath + lcf_years[year] + '/tab/' + lcf_years[year] + '_rawhh_ukanon.tab'
    rawhh[year] = pd.read_csv(rawhh_file, sep='\t', index_col=0, encoding='latin1').reset_index()
    rawhh[year].columns = rawhh[year].columns.str.lower()
    dvhh[year] = pd.read_csv(dvhh_file, sep='\t', index_col=0).reset_index()
    dvhh[year].columns = dvhh[year].columns.str.lower()

# Extract flydest data and link to weights to estimate number of flights
flight_data = {}; flight_total = {}; flight_exp = {}
for year in years:
    # also separate weight to ensure new totals are correctly weighted   
    if year < 2013:
        flight_exp[year] = dvhh[year].set_index('case')[['weighta', 'c73311t', 'c73312t']]
    else: 
        flight_exp[year] = dvhh[year].set_index('case')[['weighta', 'b487', 'b488']]
    flight_exp[year].columns = ['weight', '7.3.4.1', '7.3.4.2']
    
    temp = rawhh[year].columns.tolist()
    flights = []
    for item in temp:
        if 'flydest' in item:
            flights.append(item)
    
    flight_data[year] = pd.DataFrame(rawhh[year].set_index('case')[flights].unstack())\
        .reset_index().rename(columns={0:'Code'})
    
    # add weights
    temp2 = flight_lookup.loc[flight_lookup['Year'] == year]
    temp2['Code'] = temp2['Code'].astype(str)
    
    temp2 = flight_data[year].merge(temp2, on=['Code'])
    
    temp2 = temp2.groupby(['LCF_Year', 'Year', 'Category', 'case']).sum()\
        .unstack(level='Category').fillna(0).droplevel(axis=1, level=0).reset_index().drop_duplicates().set_index('case')
    
    flight_data[year] = flight_exp[year].join(temp2[['Domestic', 'International']]).fillna(0)
    flight_data[year].loc[:, '7.3.4.1':] = flight_data[year].loc[:, '7.3.4.1':].apply(lambda x: x*flight_data[year]['weight'])
    
    flight_data[year]['7.3.4.1_proxy'] = (flight_data[year]['Domestic'] / flight_data[year]['Domestic'].sum()) * flight_data[year]['7.3.4.1'].sum()
    flight_data[year]['7.3.4.2_proxy'] = (flight_data[year]['International'] / flight_data[year]['International'].sum()) * flight_data[year]['7.3.4.2'].sum()

    flight_data[year].loc[:, '7.3.4.1':] = flight_data[year].loc[:, '7.3.4.1':].apply(lambda x: x/flight_data[year]['weight'])  
    
    flight_data[year] = flight_data[year].drop('weight', axis=1)

# save to file
writer = pd.ExcelWriter(r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/data/processed/LCFS/Controls/flights_2001-2018.xlsx')
for year in years:
    flight_data[year].to_excel(writer, sheet_name=str(year))
writer.save()