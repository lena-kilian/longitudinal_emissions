#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import copy as cp

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

years = list(range(2001, 2019))

lcf_years = dict(zip(years, ['2001-2002', '2002-2003', '2003-2004', '2004-2005', '2005-2006', '2006', '2007', '2008', '2009', 
                             '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))

vars_og = ['a003', 'a0031', 'a004', 'a005p', 'a006p', 'a007']
vars_new = ['Household Reference Person', 'Partner of Household Reference Person', 'Sex', 'Age - anonymised', 'Marital status', 'Current full time education']

# import data
person = {}
for year in [2007, 2008, 2009]:
    dvper_file = wd + 'data/raw/LCFS/' + lcf_years[year] + '/tab/' + lcf_years[year] + '_dvper_ukanon.tab'
    dvper = pd.read_csv(dvper_file, sep='\t', index_col=None)
    dvper.columns = [x.lower() for x in dvper.columns]
    person[year] = dvper[['case', 'person'] + vars_og]
    person[year] = person[year].rename(columns=dict(zip(vars_og, vars_new))).set_index('case')
    person[year] = person[year].apply(lambda x: pd.to_numeric(x, errors='coerce'))

    min_age = person[year].groupby('case').min()[['Age - anonymised']].rename(columns={'Age - anonymised':'min_age'})
    max_age = person[year].groupby('case').max()[['Age - anonymised']].rename(columns={'Age - anonymised':'max_age'})
    
    age_group = min_age.join(max_age)
    age_group['age_group'] = 'Other'
    age_group.loc[age_group['min_age'] < 18, 'age_group'] = 'Household with children'
    age_group.loc[age_group['min_age'] >= 70, 'age_group'] = '70+'
    
    for i in [[18, 29], [30, 39], [40, 49], [50, 59], [60, 69]]:
    #for i in [[18, 29], [30, 44], [45, 60], [60, 69]]:
        age_group.loc[(age_group['min_age'] >= i[0]) & (age_group['max_age'] <= i[1]), 'age_group'] = str(i[0]) + '-' + str(i[1])
    
    students = cp.copy(person[year])
    students.loc[students['Current full time education'] != 0, 'Current full time education'] = 1
    temp = students.groupby('case').count()[['person']].rename(columns = {'person':'count'})
    students = students.groupby('case').sum()[['Current full time education']].join(temp)
    students['student_hhld'] = 'Not all students'
    students.loc[students['Current full time education'] == students['count'], 'student_hhld'] = 'All students'
    
    person[year] = person[year].reset_index()[['case']].drop_duplicates().set_index('case').join(age_group[['age_group']]).join(students[['student_hhld']])
    
    person[year].reset_index().to_csv(wd + 'data/processed/LCFS/Socio-demographic/person_variables_' + str(year) + '.csv')