#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 7 15:46:00 2020

This file controls for physical use of flights, dwellings, and electricity in the LCFS

@author: Lena Kilian
"""

import pandas as pd
from sys import platform

# set working directory
# make different path depending on operating system
if platform[:3] == 'win':
    wd = 'C:/Users/geolki/Documents/PhD/Analysis/'
else:
    wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds//PhD/Analysis'

# Dwellings

lcf_filepath = wd + 'data/raw/LCFS/'

years = list(range(2001, 2021))
lcf_years = ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019', '2019-2020',
             '2020-2021']




dvhh = {}; rent = {}; writer = pd.ExcelWriter(wd + 'data/processed/LCFS/Controls/rent_2001-2020.xlsx')
for year in lcf_years:
    dvhh_file = lcf_filepath + year + '/tab/' + year + '_dvhh_ukanon.tab'
    first_year = eval(year[:4])
    dvhh[first_year] = pd.read_csv(dvhh_file, sep='\t', index_col=0)
    dvhh[first_year].columns = dvhh[first_year].columns.str.lower()
    
    rent[first_year] = dvhh[first_year][['weighta']]
    rent[first_year]['owned_code'] = dvhh[first_year]['a121'] # 1-4 are rented
    rent[first_year]['rented_prop'] = 0
    rent[first_year].loc[(rent[first_year]['owned_code'] >= 1) & (rent[first_year]['owned_code'] <= 4), 'rented_prop'] = 1
    # split 
    rent[first_year].loc[(rent[first_year]['owned_code'] == 0) | (rent[first_year]['owned_code'] == 8), 'rented_prop'] = 0.5
    rent[first_year]['owned_prop'] = abs(rent[first_year]['rented_prop'] - 1)
    rent[first_year]['rent_dwelling_1'] = dvhh[first_year]['b010']+dvhh[first_year]['b020']
    rent[first_year]['rent_dwelling_2'] = dvhh[first_year]['c41211t']
    # adjust to weight to ensure totals are correct
    rent[first_year].loc[:,'rented_prop':] = rent[first_year].loc[:,'rented_prop':].apply(lambda x:x*rent[first_year]['weighta'])
    
    if first_year < 2005:
        rent[first_year]['room_no'] = dvhh[first_year]['a114']
    else:
        rent[first_year]['room_no'] = dvhh[first_year]['a114p']
    
    rent[first_year]['4.1.2_proxy'] = rent[first_year]['owned_prop'] * rent[first_year]['room_no']
    
    temp = rent[first_year]['rented_prop'] * rent[first_year]['room_no']
    rent[first_year]['4.1.1_proxy'] = (temp/temp.sum() * rent[first_year]['rent_dwelling_1'].sum()) + rent[first_year]['rent_dwelling_2']
    # divide by weightto get back to household level
    rent[first_year].loc[:,'rented_prop':] = rent[first_year].loc[:,'rented_prop':].apply(lambda x:x/rent[first_year]['weighta'])
    # save
    rent[first_year][['4.1.1_proxy', '4.1.2_proxy']].reset_index().to_excel(writer, sheet_name=str(first_year))
writer.save()
