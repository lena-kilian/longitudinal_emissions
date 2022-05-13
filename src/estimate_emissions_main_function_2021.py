#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 2021

CO2 emissions for MSOAs or LSOAs combining 2 years at a time, IO part adapted from code by Anne Owen

@author: lenakilian
"""

import pandas as pd
import pickle
import numpy as np

df = pd.DataFrame

################
# IO functions #
################

def make_Z_from_S_U(S,U):
    
    Z = np.zeros(shape = (np.size(S,0)+np.size(U,0),np.size(S,1)+np.size(U,1)))
    
    Z[np.size(S,0):,0:np.size(U,1)] = U
    Z[0:np.size(S,0),np.size(U,1):] = S
        
    return Z


def make_x(Z,Y):
    
    x = np.sum(Z,1)+np.sum(Y,1)
    x[x == 0] = 0.000000001
    
    return x


def make_L(Z,x):
    
    bigX = np.zeros(shape = (len(Z)))    
    bigX = np.tile(np.transpose(x),(len(Z),1))
    A = np.divide(Z,bigX)    
    L = np.linalg.inv(np.identity(len(Z))-A)

    return L

####################
# demand functions #
####################

def make_Yhh_106(Y_d,years,meta):
    
    total_Yhh_106 = {}
    col =  Y_d[years[0]].columns[0:36]
    idx =  Y_d[years[0]].index[0:106]
    for yr in years:
        temp = np.zeros(shape = [106,36])
        
        for r in range(0,meta['reg']['len']):
            temp  = temp + Y_d[yr].iloc[r*106:(r+1)*106,0:36].values
            
        total_Yhh_106[yr] = df(temp, index =idx, columns =col)
    
    return total_Yhh_106


def make_Yhh_112(Y_d,years,meta):
    
    total_Yhh_112 = {}
    col =  Y_d[years[0]].columns[0:36]
    idx =  Y_d[years[0]].index[0:112]
    for yr in years:
        temp = np.zeros(shape = [112,36])
        
        for r in range(0,meta['reg']['len']):
            temp  = temp + Y_d[yr].iloc[r*112:(r+1)*112,0:36].values
            
        total_Yhh_112[yr] = df(temp, index =idx, columns =col)
    
    return total_Yhh_112

##################
# LCFS functions #
##################

def convert36to33(Y,concs_dict2,years):
    
    Y2 = {}
    
    for yr in years:
        temp = np.dot(Y[yr],concs_dict2['C43_to_C40'])
        Y2[yr] = df(temp, index = Y[yr].index, columns = concs_dict2['C43_to_C40'].columns)
    
    return Y2

def expected_totals(hhspenddata, years, concs_dict2, total_Yhh_106):
    coicop_exp_tot = {}
    for year in years:
        temp = np.sum(hhspenddata[year], 0)

        corrector = np.zeros(shape = 307)
        start = 0
        end = 0
        corrector = []
    
        for i in range(0, 33):
            conc = concs_dict2[str(i) + 'a']
            end = len(conc.columns) + start
            lcf_subtotal = np.sum(np.dot(temp, conc))
            required_subtotal = np.sum(total_Yhh_106[year].iloc[:, i])
            corrector += [required_subtotal/lcf_subtotal for i in range(start, end)]
            start = end
        coicop_exp_tot[year] = np.dot(temp, np.diag(corrector))  
        
    return(coicop_exp_tot)

def make_y_hh_307(Y,coicop_exp_tot,years,concs_dict2,meta):
    
    yhh_wide = {}
    
    for yr in years:
        temp = np.zeros(shape = [meta['fd']['len_idx'],307])
        countstart = 0
        countend = 0
        col = []
        for a in range(0,33):
            conc = np.tile(concs_dict2[str(a)],(meta['reg']['len'],1))
            countend = np.sum(np.sum(concs_dict2[str(a)+'a']))+countstart
            category_total = np.dot(coicop_exp_tot[yr],concs_dict2[str(a)+'a'])
            #test1 = np.dot(np.diag(Y[yr].iloc[:,a]),conc)
            test1 = np.dot(conc,np.diag(category_total))
            #test2 = np.tile(np.dot(Y[yr].iloc[:,a],conc),(1590,1))
            test2 = np.transpose(np.tile(np.dot(conc,category_total),(np.size(conc,1),1)))
            test3 = test1/test2
            test3 = np.nan_to_num(test3, copy=True)
            #num = np.dot(conc,np.diag(category_total))
            #test4 = np.multiply(num,test3)
            test4 = np.dot(np.diag(Y[yr].iloc[:,a]),test3)
            #den = np.dot(np.diag(np.sum(num,1)),concs_dict2[str(a)])
            #prop = np.divide(num,den)
            #prop = np.nan_to_num(prop, copy=True)
            #temp[:,countstart:countend] = (np.dot(np.diag(total_Yhh_106[yr].iloc[:,a]),prop))
            temp[:,countstart:countend] = test4
            col[countstart:countend] = concs_dict2[str(a) + 'a'].columns
            countstart = countend
        yhh_wide[yr] = df(temp, columns = col)
            
    return yhh_wide


def make_y_hh_prop(Y,total_Yhh_106,meta,years):
    
    yhh_prop = {}
    
    for yr in years:
        temp = np.zeros(shape=(len(Y[yr])))
    
        for r in range(0,meta['reg']['len']):
            temp[r*106:(r+1)*106] = np.divide(np.sum(Y[yr].iloc[r*106:(r+1)*106,0:36],1),np.sum(total_Yhh_106[yr],1))
            np.nan_to_num(temp, copy = False)
        
        yhh_prop[yr] = temp

        
    return yhh_prop


def make_new_Y(Y,yhh_wide,meta,years):
    
    newY = {}
    col = []
    
    for yr in years:
        temp = np.zeros(shape=[len(Y[yr]),314])
        temp[:,0:307] = yhh_wide[yr]
        temp[:,307:314] = Y[yr].iloc[:,33:40]
        col[0:307] = yhh_wide[yr].columns
        col[307:314] = Y[yr].iloc[:,33:40].columns
        newY[yr] = df(temp, index = Y[yr].index, columns = col)
    
    return newY

def make_ylcf_props(hhspenddata,years):
    
    ylcf_props = {}
    
    for yr in years:
        totalspend = np.sum(hhspenddata[yr].loc[:,'1.1.1.1':'12.5.3.5'])
        temp = np.divide(hhspenddata[yr].loc[:,'1.1.1.1':'12.5.3.5'],np.tile(totalspend,[len(hhspenddata[yr]),1]))
        np.nan_to_num(temp, copy = False)
        ylcf_props[yr] = df(temp, index = hhspenddata[yr].index)
        
    return ylcf_props


def makefoot(S,U,Y,stressor,years):
    footbyCOICOP = {}
    for yr in years:
        temp = np.zeros(shape = 307)
        Z = make_Z_from_S_U(S[yr],U[yr]) 
        bigY = np.zeros(shape = [np.size(Y[yr],0)*2,np.size(Y[yr],1)])
        bigY[np.size(Y[yr],0):np.size(Y[yr],0)*2,0:] = Y[yr]     
        x = make_x(Z,bigY)
        L = make_L(Z,x)
        bigstressor = np.zeros(shape = [np.size(Y[yr],0)*2,1])
        bigstressor[0:np.size(Y[yr],0),:] = stressor[yr]
        e = np.sum(bigstressor,1)/x
        eL = np.dot(e,L)
        for a in range(0,307):
            temp[a] = np.dot(eL,bigY[:,a])
        footbyCOICOP[yr] = temp  

    return footbyCOICOP

###########
# Run all #
###########

def make_footprint(hhdspend, wd):
    
    """
    Calculate consumption-based household GHG emissions for MSOAs or LSOAs from the LCFS (emissios calculated in LCFS_aggregation_combined_years.py) and the UKMRIO 2020
    """

#############
# load data #
#############

    # load meta data from [UKMRIO]
    meta = pickle.load(open(wd + 'data/raw/UKMRIO_2021/meta.p', "rb" ))
   
    # create year lists
    years = list(hhdspend.keys())

    # load and clean up concs to make it usable
    # these translate IO data sectors to LCFS products/services
    concs_dict2 = pd.read_excel(wd + 'data/raw/Concordances/ONS_to_COICOP_LCF_concs_2021.xlsx', sheet_name=None, index_col=0)

#######################
# aggregate emissions #
#######################

    # get mean from 2 years
    # calculate differnece between years in household data to calculate means for other vairables
    
    # Load UKMRIO and calculate means for UKMRIO data
    ukmrio = {}; #means = {}
    for data in ['ghg', 'uk_ghg_direct', 'S', 'U', 'Y']:
        ukmrio[data] = pickle.load(open(wd + 'data/raw/UKMRIO_2021/' + data + '.p', "rb" ))
        
    ukmrio['Y'] = convert36to33(ukmrio['Y'], concs_dict2, years)
    total_Yhh_112 = make_Yhh_112(ukmrio['Y'], years, meta)
    
    coicop_exp_tot = expected_totals(hhdspend, list(hhdspend.keys()), concs_dict2, total_Yhh_112)

    yhh_wide = make_y_hh_307(ukmrio['Y'], coicop_exp_tot, list(hhdspend.keys()), concs_dict2, meta)
    newY = make_new_Y(ukmrio['Y'], yhh_wide, meta, list(hhdspend.keys()))

    ylcf_props = make_ylcf_props(hhdspend, list(hhdspend.keys()))

    COICOP_ghg = makefoot(ukmrio['S'], ukmrio['U'], newY, ukmrio['ghg'], list(hhdspend.keys()))

    Total_ghg = {}; multipliers = {}
    for year in list(hhdspend.keys()):
        COICOP_ghg[year][160] += ukmrio['uk_ghg_direct'][year][1]
        COICOP_ghg[year][101] += ukmrio['uk_ghg_direct'][year][0]
        
        # multipliers tCO2e/GBP 
        multipliers[year] = df(COICOP_ghg[year], columns=['total_ghg'], index=hhdspend[year].columns)
        multipliers[year]['total_spend'] = hhdspend[year].sum(0)
        multipliers[year]['multipliers'] = multipliers[year]['total_ghg'] / multipliers[year]['total_spend']
    
        # this gives GHG emissions for the groups, break down to per capita emissions
        temp = np.dot(ylcf_props[year], np.diag(COICOP_ghg[year]))
        Total_ghg[year] = df(temp, index=hhdspend[year].index, columns=hhdspend[year].columns)
    
    return(Total_ghg, multipliers)