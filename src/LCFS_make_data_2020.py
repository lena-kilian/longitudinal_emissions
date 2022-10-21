#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Import hhld expenditure data and adjust physical units 2001-2018

@author: lenakilian

Before this run:
    1. LCFS_PhysicalUnits_Flights.py
    2. LCFS_PhysicalUnits_Rent.py
    3. LCFS_import_data_function.py
    
Next run: LCFS_estimate_emissions.py
"""

import pandas as pd
import LCFS_import_data_function as lcfs_import
import copy as cp

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

# Load LCFS data
dvhh_file = wd + 'data/raw/LCFS/2019-2020/tab/2019-2020_dvhh_ukanon.tab'
dvper_file = wd + 'data/raw/LCFS/2019-2020/tab/2019-2020_dvper_ukanon.tab'

lcfs_2019 = lcfs_import.import_lcfs(2019, dvhh_file, dvper_file).drop_duplicates()
lcfs_2019 = lcfs_2019.reset_index()
lcfs_2019.columns = [x.lower() for x in lcfs_2019.columns]
lcfs_2019 = lcfs_2019.set_index('case')  
lcfs_2019.loc[:,'1.1.1.1':] = lcfs_2019.loc[:,'1.1.1.1':].apply(lambda x:x*lcfs_2019['weight'])
lcfs_2019 = lcfs_2019.sum()

total_lcfs_2019 = lcfs_2019.loc['1.1.1.1':'12.5.3.5'].sum() / lcfs_2019['weight']
total_ons_2019 = 509 # sum of average expenditure ons data

multiplier = total_lcfs_2019/total_ons_2019
    
# import 2020 data
ons_2020 = pd.read_excel(wd + 'data/raw/LCFS/LCFS_aggregated_2020.xlsx', sheet_name='Exp_adj_LCFS', index_col=0, header=[0, 1])\
    [['All', 'Income decile', 'Age of HRP']].T.fillna(0)
# adjust 2020 data to multiplier
lcfs_2020 = ons_2020.loc[:,:'1.1.1.1'].iloc[:,:-1].join(ons_2020.loc[:,'1.1.1.1':] * multiplier)

lcfs_2020.to_csv(wd + 'data/raw/LCFS/LCFS_aggregated_2020_adjusted.csv')

