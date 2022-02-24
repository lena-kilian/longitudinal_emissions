#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 14:19:05 2020

Functions to attach the LCFS to carbon emissions, based on code by Anne Owen

@author: lenakilian
"""

import numpy as np
import pandas as pd


def import_lcfs(year, dvhh_file, dvper_file):
    
    idx = {}; idx['person'] = {}; idx['hhld'] = {}

    idx['person']['to_keep'] = ['person', 'a012p', 'a013p']
    idx['person']['new_name'] = ['person_no', 'ethnicity_hrp', 'ethnicity partner hrp', 'income tax']
    idx['person']['dict'] = dict(zip(idx['person']['to_keep'], idx['person']['new_name']))

    idx['hhld']['to_keep'] = ['weighta', 'p396p', 'sexhrp']
    idx['hhld']['new_name'] = ['weight', 'age HRP', 'sex HRP']
    idx['hhld']['dict'] = dict(zip(idx['hhld']['to_keep'], idx['hhld']['new_name']))
    
    dvhh = pd.read_csv(dvhh_file, sep='\t', index_col=0)
    dvper = pd.read_csv(dvper_file, sep='\t', index_col=0)
    
    dvhh.columns = dvhh.columns.str.lower()
    dvper.columns = dvper.columns.str.lower()
    
    owned_prop = np.zeros(shape = len(dvhh))
    for n in range (1,len(dvhh)):
        if dvhh['a121'].iloc[n] == 5 or dvhh['a121'].iloc[n] == 6 or dvhh['a121'].iloc[n] == 7:
            owned_prop[n] = 1
     
    person_data = dvper[idx['person']['to_keep']].rename(columns=idx['person']['dict'])
    person_data['income tax'] = np.zeros(shape=np.size(dvper,0))
    
    useful_data = dvhh[idx['hhld']['to_keep']].rename(columns=idx['hhld']['dict'])
    
    temp = useful_data.join(person_data, how = 'inner')
    temp = temp.apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0)
    
    useful_data['ethnicity HRP'] = temp.groupby(level=0)['ethnicity_hrp'].sum()
    useful_data['no people'] = dvhh['a049']
    useful_data['type of hhold'] = dvhh['a062']
    useful_data['category of dwelling'] = dvhh['a116']
    useful_data['tenure type'] = dvhh['a122']
    useful_data['GOR modified'] = dvhh['gorx']
    useful_data['OA class 1D'] =  np.zeros(shape=len(dvhh))
    # OAC data only available from 2007
    if year > 2006: 
        useful_data['OAC_Supergroup'] = dvhh['oac1d']
        useful_data['OAC_Group'] = dvhh['oac2d']
        useful_data['OAC_Subgroup'] = dvhh['oac3d']
    useful_data['Income anonymised'] = dvhh['incanon']
    useful_data['Income tax'] = temp.groupby(level=0)['income tax'].sum()
    useful_data['Socio-ec HRP'] = dvhh['a091']
    
    # add family information
    family_code = ['a016','a017', 'a018', 
                   'a020', 'a021', 'a022', 'a023', 'a024', 'a025', 'a026', 'a027', 
                   'a030', 'a031', 'a032', 'a033', 'a034', 'a035', 'a036', 'a037', 
                   'a040', 'a041', 'a042', 'a043', 'a044', 'a045', 'a046', 'a047',
                   'a0423']
    
    family_name = ['Males aged 16-17', 'Females aged 16-17', 'People aged 16-17', 
                   
                   'Males aged <2', 'Males aged 2-4', 'Males aged 5-17', 'Males aged 18-44', 'Males aged 45-59', 
                   'Males aged 60-64', 'Males aged 65-69', 'Males aged >69', 
                   
                   'Females aged <2', 'Females aged 2-4', 'Females aged 5-17', 'Females aged 18-44', 'Females aged 45-59', 
                   'Females aged 60-64', 'Females aged 65-69', 'Females aged >69', 
                   
                   'People aged <2', 'People aged 2-4', 'People aged 5-17', 'People aged 18-44', 'People aged 45-59', 
                   'People aged 60-64', 'People aged 65-69', 'People aged >69',
                   
                   'Number of children completing a diary']
    
    for i in range(len(family_code)):
        useful_data[family_name[i]] = dvhh[family_code[i]]
        
    useful_data['Males aged 5-15'] = useful_data['Males aged 5-17'] - useful_data['Males aged 16-17']
    useful_data['Females aged 5-15'] = useful_data['Females aged 5-17'] - useful_data['Females aged 16-17']
    useful_data['People aged 5-15'] = useful_data['People aged 5-17'] - useful_data['People aged 16-17']
    useful_data = useful_data.drop(['Males aged 5-17', 'Females aged 5-17', 'People aged 5-17'], axis=1)

  
    if year < 2005:
        useful_data['rooms in accommodation'] = dvhh['a114']
    else:
        useful_data['rooms in accommodation'] = dvhh['a114p']
    
    # 1
    coicop = ['1.1.1.1','1.1.1.2', '1.1.1.3', '1.1.2', '1.1.3.1', '1.1.3.2', '1.1.4', '1.1.5', '1.1.6', '1.1.7',
              '1.1.8', '1.1.9', '1.1.10.1', '1.1.10.2', '1.1.10.3', '1.1.10.4', '1.1.11.1', '1.1.11.2', '1.1.11.3', '1.1.12.1',
              '1.1.12.2', '1.1.12.3', '1.1.13', '1.1.14', '1.1.15.1', '1.1.15.2', '1.1.16', '1.1.17', '1.1.18.1', '1.1.18.2', 
              '1.1.19.1', '1.1.19.2', '1.1.19.3', '1.1.19.4', '1.1.19.5', '1.1.19.6', '1.1.20', '1.1.21', '1.1.22', '1.1.23.1', 
              '1.1.23.2', '1.1.23.3', '1.1.23.4', '1.1.24', '1.1.25', '1.1.26', '1.1.27', '1.1.28.1', '1.1.28.2', '1.1.29', 
              '1.1.30', '1.1.31', '1.1.32', '1.1.33.1', '1.1.33.2', '1.1.33.3', '1.2.1', '1.2.2', '1.2.3', '1.2.4', 
              '1.2.5', '1.2.6']
    variables = [['c11111t'], ['c11121t'], ['c11151t'], ['c11131t'], ['c11122t'], ['c11141t'], ['c11142t'], ['c11211t'], ['c11221t'], ['c11231t'], 
                 ['c11241t'], ['c11252t'], ['c11251t'], ['c11253t'], ['c11261t'], ['c11271t'], ['c11311t'], ['c11321t', 'c11331t'], ['c11341t'], ['c11411t'],
                 ['c11421t'], ['c11431t'], ['c11451t'], ['c11471t'], ['c11461t'], ['c11441t'], ['c11511t'], ['c11521t', 'c11522t'], ['c11531t'], ['c11541t', 'c11551t'],
                 ['c11611t'], ['c11621t'], ['c11631t'], ['c11641t'], ['c11651t'], ['c11661t'], ['c11671t'], ['c11681t'], ['c11691t'], ['c11711t'],
                 ['c11721t'], ['c11731t'], ['c11741t'], ['c11751t'], ['c11761t'], ['c11771t'], ['c11781t'], ['c11811t'], ['c11861t'], ['c11821t'],
                 ['c11831t'], ['c11841t'], ['c11851t'], ['c11911t'], ['c11931t'], ['c11921t', 'c11941t'], ['c12111t'], ['c12121t'], ['c12131t'], ['c12231t', 'c12241t'],
                 ['c12211t'], ['c12221t']]
    
    
    for i in range(len(coicop)):
        useful_data[coicop[i]] = dvhh[variables[i]].sum(1)
    
    # 2
    coicop = ['2.1.1', '2.1.2.1', '2.1.2.2', '2.1.2.3', '2.1.3.1', '2.1.3.2', '2.1.4', '2.2.1', '2.2.2.1', '2.2.2.2']
    variables = [['c21111t'], ['c21211t'], ['c21212t'], ['c21221t'], ['c21211t'], ['c21213t'], ['c21214t'], ['c22111t'], ['c22121t'], ['c22131t']]
    
    for i in range(len(coicop)):
        useful_data[coicop[i]] = dvhh[variables[i]].sum(1)   
    
    # 3
    coicop = ['3.1.1', '3.1.2', '3.1.3', '3.1.4', '3.1.5', '3.1.6', '3.1.7', '3.1.8', '3.1.9.1', '3.1.9.2',
              '3.1.9.3', '3.1.9.4', '3.1.10', '3.1.11.1', '3.1.11.2', '3.2.1', '3.2.2', '3.2.3', '3.2.4']
    variables = [['c31211t'], ['c31212t'], ['c31221t'], ['c31222t'], ['c31231t'], ['c31232t'], ['c31233t'], ['c31234t'], ['c31311t'], ['c31312t'],
                 ['c31313t'], ['c31315t'], ['c31111t', 'c31314t', 'c31411t'], ['c31412t'], ['c31413t'], ['c32111t'], ['c32121t'], ['c32131t'], ['c32211t']]
    
    for i in range(len(coicop)):
        useful_data[coicop[i]] = dvhh[variables[i]].sum(1)
    

    # 4
    useful_data['4.1.1'] = (dvhh['b010']+dvhh['b020']+dvhh['c41211t']) # first dwelling rent dvhh['b010']+dvhh['b020'] AND second dwelling rent dvhh['c41211t']
    if year < 2005:
        useful_data['4.1.2'] = dvhh['a114']*owned_prop #imputed rentals = no of rooms times 1 if owner occupied
    else:
        useful_data['4.1.2'] = dvhh['a114p']*owned_prop #imputed rentals = no of rooms times 1 if owner occupied
    # useful_data['4.1.4'] = dvhh['c41211t'] # second dwelling rent: only use if separating from first dwelling
    useful_data['4.2.1'] = (dvhh['b102']+dvhh['b104'])
    useful_data['4.2.2'] = (dvhh['b107']+dvhh['b108']+dvhh['c43212c'])
    useful_data['4.2.3'] = dvhh['c43111t']
    useful_data['4.2.4'] = dvhh['c43112t']
    useful_data['4.3.1'] = (dvhh['b050']+dvhh['b053p']+dvhh['b056p'])
    useful_data['4.3.2'] = (dvhh['b060']+dvhh['b159'])
    useful_data['4.3.3'] = dvhh['c44211t']
    if year < 2009:
        useful_data['4.4.1'] = (dvhh['b175']+dvhh['p250t']+dvhh['c45112t']+dvhh['b222'])
        useful_data['4.4.2'] = (dvhh['b018']+dvhh['b170']+dvhh['p249t']+dvhh['b221']+dvhh['c45212t']+dvhh['c45222t'])
    elif year >= 2009 and year <2013:
        useful_data['4.4.1'] = (dvhh['b175']+dvhh['p250t']+dvhh['c45112t']+dvhh['b224'])
        useful_data['4.4.2'] = (dvhh['b018']+dvhh['b170']+dvhh['p249t']+dvhh['b223']+dvhh['c45212t']+dvhh['c45222t'])
    elif year >= 2013 and year <2015:
        useful_data['4.4.1'] = (dvhh['b489']+dvhh['b227']+dvhh['b254']+dvhh['b234']+dvhh['c45112t']+dvhh['b491']+dvhh['b2241'])
        useful_data['4.4.2'] = (dvhh['b490']+dvhh['b226']+dvhh['b255']+dvhh['b235']+dvhh['c45212t']+dvhh['b492']+dvhh['b2231']+dvhh['b018']+dvhh['c45222t'])
    else:
        useful_data['4.4.1'] = (dvhh['b489']+dvhh['b227']+dvhh['b254']+dvhh['b234']+dvhh['c45112t'])
        useful_data['4.4.2'] = (dvhh['b490']+dvhh['b226']+dvhh['b255']+dvhh['b235']+dvhh['c45212t']+dvhh['b018']+dvhh['c45222t'])
    useful_data['4.4.3.1'] = dvhh['c45411t']
    useful_data['4.4.3.2'] = dvhh['b017']
    useful_data['4.4.3.3'] = (dvhh['c45312t']+dvhh['c45412t']+dvhh['c45511t'])
    
    
    # 5
    useful_data['5.1.1.1'] = (dvhh['b270']+dvhh['c51111c'])
    useful_data['5.1.1.2'] = dvhh['c51113t']
    useful_data['5.1.1.3'] = dvhh['c51114t']
    useful_data['5.1.2.1'] = (dvhh['b271']+dvhh['c51211c'])
    useful_data['5.1.2.2'] = dvhh['c51212t']
    useful_data['5.2.1'] = dvhh['c52111t']
    useful_data['5.2.2'] = dvhh['c52112t']
    useful_data['5.3.1'] = dvhh['c53131t']
    useful_data['5.3.2'] = dvhh['c53132t']
    useful_data['5.3.3'] = dvhh['c53121t']
    useful_data['5.3.4'] = dvhh['c53111t']
    useful_data['5.3.5'] = (dvhh['c53122t']+dvhh['c53133t']+dvhh['c53141t']+dvhh['c53151t']+dvhh['c53161t'])
    useful_data['5.3.6'] = dvhh['c53171t']
    useful_data['5.3.7'] = dvhh['c53211t']
    useful_data['5.3.8'] = (dvhh['c53311t']+dvhh['c53312t']+dvhh['c53313t'])
    if year == 2001:
        useful_data['5.3.9'] = np.zeros(shape=np.size(dvhh,0))
    else:
        useful_data['5.3.9'] = dvhh['c53314t']
    useful_data['5.4.1'] = (dvhh['c54111t']+dvhh['c54121t'])
    useful_data['5.4.2'] = dvhh['c54131t']
    useful_data['5.4.3'] = dvhh['c54141t']
    if year == 2001:
        useful_data['5.4.4'] = np.zeros(shape=np.size(dvhh,0))
    else:
        useful_data['5.4.4'] = dvhh['c54132t']
    useful_data['5.5.1'] = dvhh['c55111t']
    useful_data['5.5.2'] = (dvhh['c55112t']+dvhh['c55213t'])
    useful_data['5.5.3'] = dvhh['c55211t']
    useful_data['5.5.4'] = dvhh['c55212t']
    useful_data['5.5.5'] = dvhh['c55214t']
    useful_data['5.6.1.1'] = dvhh['c56111t']
    useful_data['5.6.1.2'] = dvhh['c56112t']
    useful_data['5.6.2.1'] = dvhh['c56121t']
    useful_data['5.6.2.2'] = dvhh['c56122t']
    if year == 2001:
        useful_data['5.6.2.3'] = np.zeros(shape=np.size(dvhh,0))
    else:
        useful_data['5.6.2.3'] = dvhh['c56123t']
    useful_data['5.6.2.4'] = (dvhh['c56124t']+dvhh['c56125t'])
    useful_data['5.6.3.1'] = dvhh['c56211t']
    useful_data['5.6.3.2'] = (dvhh['c56221t']+dvhh['c56222t'])
    if year == 2001:
        useful_data['5.6.3.3'] = (dvhh['c51311t'])
    else:
        useful_data['5.6.3.3'] = (dvhh['c56223t']+dvhh['c51311t'])
    
    
    # 6
    coicop = ['6.1.1.1', '6.1.1.2', '6.1.1.3', '6.1.1.4', '6.1.2.1', '6.1.2.2', '6.2.1.1', '6.2.1.2', '6.2.1.3', '6.2.2']
    variables = [['c61111t'], ['c61112t'], ['c61211t'], ['c61313t'], ['c61311t'], ['c61312t'], ['c62111t', 'c62113t', 'c62321t', 'c62211t'], ['c62112t', 'c62114t', 'c62212t', 'c62322t'], ['c62311t', 'c62331t'], ['c63111t']]

    for i in range(len(coicop)):
        useful_data[coicop[i]] = dvhh[variables[i]].sum(1)
    
    
    # 7
    if year < 2013:
        coicop = ['7.1.1.1', '7.1.1.2', '7.1.2.1', '7.1.2.2', '7.1.3.1', '7.1.3.2', '7.1.3.3', '7.2.1.1', '7.2.1.2', '7.2.1.3',
                  '7.2.1.4', '7.2.2.1', '7.2.2.2', '7.2.2.3', '7.2.3.1', '7.2.3.2', '7.2.4.1', '7.2.4.2', '7.2.4.3', '7.2.4.4',
                  '7.2.4.5', '7.3.1.1', '7.3.1.2', '7.3.2.1', '7.3.2.2', '7.3.3.1', '7.3.3.2', '7.3.4.1', '7.3.4.2', '7.3.4.3',
                  '7.3.4.4', '7.3.4.5', '7.3.4.6', '7.3.4.7', '7.3.4.8']
        variables = [['b244', 'c71111c'], ['c71112t'], ['b245', 'c71121c'], ['c71122t'], ['b247', 'c71211c'], ['c71212t'], ['c71311t', 'c71411t'], ['c72111t'], ['c72112t'], ['c72113t'],
                     ['c72115t'], ['c72211t'], ['c72212t'], ['c72213t'], ['c72311c', 'b249', 'b250'], ['c72312c', 'b252'], ['c72313t'], ['c72314t', 'c72412t'], ['c72411t'], ['c72413t'],
                     ['c72414t'], ['b218'], ['c73112t'], ['b217'], ['c73212t'], ['c73512t'], ['b216'], ['c73311t'], ['c73312t'], ['c73513t'],
                     ['c73213t'], ['c73214t', 'c73611t'], ['c72414t'], ['b248'], ['b219', 'c73411t']]
    else:
        coicop = ['7.1.1.1', '7.1.1.2', '7.1.2.1', '7.1.2.2', '7.1.3.1', '7.1.3.2', '7.1.3.3', '7.2.1.1', '7.2.1.2', '7.2.1.3',
                  '7.2.1.4', '7.2.2.1', '7.2.2.2', '7.2.2.3', '7.2.3.1', '7.2.3.2', '7.2.4.1', '7.2.4.2', '7.2.4.3', '7.2.4.4',
                  '7.2.4.5', '7.3.1.1', '7.3.1.2', '7.3.2.1', '7.3.2.2', '7.3.3.1', '7.3.3.2', '7.3.4.1', '7.3.4.2', '7.3.4.3',
                  '7.3.4.4', '7.3.4.5', '7.3.4.6', '7.3.4.7', '7.3.4.8']
        variables = [['b244', 'c71111c'], ['c71112t'], ['b245', 'c71121c'], ['c71122t'], ['b247', 'c71211c'], ['c71212t'], ['c71311t', 'c71411t'], ['c72111t'], ['c72112t'], ['c72113t'],
                     ['c72115t'], ['c72211t'], ['c72212t'], ['c72213t'], ['c72311c', 'b249', 'b250'], ['c72312c', 'b252'], ['c72313t'], ['c72314t', 'c72412t'], ['c72411t'], ['c72413t'],
                     ['c72414t'], ['b218'], ['c73112t'], ['b217'], ['c73212t'], ['c73512t'], ['b216'], ['b487'], ['b488'], ['c73513t'],
                     ['c73213t'], ['c73214t', 'c73611t'], ['c72414t'], ['b248'], ['b219', 'c73411t']]
    
    
    for i in range(len(coicop)):
        useful_data[coicop[i]] = dvhh[variables[i]].sum(1)
    
    # 8
    useful_data['8.1'] = dvhh['c81111t']
    useful_data['8.2.1'] = dvhh['c82111t']
    useful_data['8.2.2'] = dvhh['c82112t']
    useful_data['8.2.3'] = dvhh['c82113t']
    if year != 2018:
        useful_data['8.3.1'] = (dvhh['b166']+dvhh['c83111c']+dvhh['c83115t'])
    else:
        useful_data['8.3.1'] = (dvhh['b166b']+dvhh['c83111c']+dvhh['c83115t'])
    useful_data['8.3.2'] = dvhh['c83112t']
    if year != 2018:
        useful_data['8.3.3'] = (dvhh['b1661']+dvhh['c83113c'])
    else:
        useful_data['8.3.3'] = (dvhh['b1661b']+dvhh['c83113c'])
    useful_data['8.3.4'] = dvhh['c83114t']
    if year < 2013:
        useful_data['8.4'] = dvhh['c94245t']
    elif year >=2013 and year < 2018:
        useful_data['8.4'] = dvhh['b195']
    else:
        useful_data['8.4'] = dvhh['b195b']
    
    
    # 9
    useful_data['9.1.1.1'] = (dvhh['c91111t']+dvhh['c91112t'])
    useful_data['9.1.1.2'] = (dvhh['c91113t']+dvhh['c91411t'])
    useful_data['9.1.2.1'] = (dvhh['c91121t']+dvhh['c91125t'])
    useful_data['9.1.2.2'] = (dvhh['c91122t']+dvhh['c91123t'])
    useful_data['9.1.2.3'] = dvhh['c91127t']
    useful_data['9.1.2.4'] = dvhh['c91124t']
    if year < 2003:
        useful_data['9.1.2.5'] = np.zeros(shape=np.size(dvhh,0))
    else:
        useful_data['9.1.2.5'] = dvhh['c91128t']
    if year < 2005:
        useful_data['9.1.2.6'] = dvhh['c91412t']
    else:
        useful_data['9.1.2.6'] = (dvhh['c91412t']+dvhh['c91414t'])
    useful_data['9.1.2.7'] = dvhh['c91311t']
    useful_data['9.1.2.8'] = dvhh['c91126t']
    useful_data['9.1.2.9'] = dvhh['c91511t']
    useful_data['9.1.3.1'] = dvhh['c91211t']
    useful_data['9.1.3.2'] = dvhh['c91413t']
    useful_data['9.1.3.3'] = dvhh['c91221t']
    useful_data['9.2.1'] = dvhh['c92111t']
    useful_data['9.2.2'] = dvhh['c92112t']
    useful_data['9.2.3'] = dvhh['c92117t']
    useful_data['9.2.4'] = dvhh['c92211t']
    useful_data['9.2.5'] = dvhh['c92221t']
    useful_data['9.2.6'] = dvhh['c92311t']
    useful_data['9.2.7'] = (dvhh['b2441']+dvhh['b2451']+dvhh['c92113c']+dvhh['c92115c'])
    useful_data['9.2.8'] = (dvhh['c92114t']+dvhh['c92116t'])
    useful_data['9.3.1'] = (dvhh['c93111t']+dvhh['c93114t'])
    useful_data['9.3.2.1'] = dvhh['c93112t']
    useful_data['9.3.2.2'] = dvhh['c93113t']
    useful_data['9.3.3'] = dvhh['c93211t']
    useful_data['9.3.4.1'] = dvhh['c93212t']
    useful_data['9.3.4.2'] = dvhh['c93311t']
    useful_data['9.3.4.3'] = dvhh['c93312t']
    useful_data['9.3.4.4'] = dvhh['c93313t']
    useful_data['9.3.5.1'] = dvhh['c93411t']
    useful_data['9.3.5.2'] = dvhh['c93412t']
    useful_data['9.3.5.3'] = dvhh['c93511t']
    useful_data['9.4.1.1'] = dvhh['c94111t']
    useful_data['9.4.1.2'] = dvhh['c94112t']
    useful_data['9.4.1.3'] = dvhh['c94113t']
    useful_data['9.4.1.4'] = (dvhh['c94114c']+dvhh['b162'])
    if year == 2001:
        useful_data['9.4.1.5'] = np.zeros(shape=np.size(dvhh,0))
    else:
        useful_data['9.4.1.5'] = dvhh['c94115t']
    useful_data['9.4.2.1'] = dvhh['c94211t']
    useful_data['9.4.2.2'] = dvhh['c94212t']
    useful_data['9.4.2.3'] = dvhh['c94221t']
    useful_data['9.4.3.1'] = (dvhh['b181']+dvhh['c94231c']+dvhh['c94232t'])
    if year != 2018:
        useful_data['9.4.3.2'] = (dvhh['b192']+dvhh['c94233c'])
        useful_data['9.4.3.3'] = (dvhh['b191']+dvhh['c94237c'])
        useful_data['9.4.3.4'] = (dvhh['b193']+dvhh['c94235c'])
    else:
        useful_data['9.4.3.2'] = (dvhh['b192b']+dvhh['c94233c'])
        useful_data['9.4.3.3'] = (dvhh['b191b']+dvhh['c94237c'])
        useful_data['9.4.3.4'] = (dvhh['b193b']+dvhh['c94235c'])
    useful_data['9.4.3.5'] = dvhh['c94236t']
    useful_data['9.4.3.6'] = (dvhh['c94238t']+dvhh['c94239t'])
    useful_data['9.4.4.1'] = dvhh['c94241t']
    useful_data['9.4.4.2'] = dvhh['c94242t']
    useful_data['9.4.4.3'] = (dvhh['c94243t']+dvhh['c94244t'])
    useful_data['9.4.5'] = dvhh['c94246t']
    useful_data['9.4.6.1'] = dvhh['c94311t']
    useful_data['9.4.6.2'] = dvhh['c94312t']
    useful_data['9.4.6.3'] = (dvhh['c94313t']+dvhh['c94315t']+dvhh['c94316t']+dvhh['c94319t'])
    useful_data['9.4.6.4'] = dvhh['c94314t']
    useful_data['9.5.1'] = dvhh['c95111t']
    useful_data['9.5.2'] = dvhh['c95411t']
    useful_data['9.5.3'] = dvhh['c95311t']
    useful_data['9.5.4'] = dvhh['c95211t']
    useful_data['9.5.5'] = dvhh['c95212t']
    
    
    # 10
    if year == 2001:
        useful_data['10.1'] = (dvhh['b160']+dvhh['b164'])
    else:
        useful_data['10.1'] = (dvhh['b1601']+dvhh['ca1111c']+dvhh['b1641']+dvhh['ca1112c']+dvhh['b1602']+dvhh['ca2111c']+dvhh['b1642']+
                               dvhh['ca2112c']+dvhh['b1603']+dvhh['ca3111c']+dvhh['b1643']+dvhh['ca3112c']+dvhh['b1604']+dvhh['ca4111c']+
                               dvhh['b1644']+dvhh['ca4112c']+dvhh['b1605']+dvhh['ca5111c']+dvhh['b1645']+dvhh['ca5112c'])
    useful_data['10.2'] = (dvhh['ca1113t']+dvhh['ca2113t']+dvhh['ca3113t']+dvhh['ca4113t']+dvhh['ca5113t'])
    
    # 11
    if year == 2001:
        coicop = ['11.1.1', '11.1.2', '11.1.3', '11.1.4.1', '11.1.4.2', '11.1.4.3', '11.1.4.4', '11.1.5', '11.1.6.1', '11.1.6.2',
                  '11.2.1', '11.2.2', '11.2.3']
        variables = [['cb1111t', 'cb1122t'], ['cb111ct', 'cb111dt', 'cb111et', 'cb111ft', 'cb111gt', 'cb111ht', 'cb111it', 'cb111jt'], 
                     ['cb1127t', 'cb1128t'], ['cb1115t', 'cb111ac', 'cb1116t', 'cb111bc', 'cb1125t', 'cb1126t'], ['cb1112t', 'cb1117c', 'cb1122t'],
                     ['cb1113t', 'cb1118c', 'cb1123t'], ['cb1114t', 'cb1119c', 'cb1124t'], ['cb112bt'], ['b260t'], ['cb1213t'],
                     ['b482', 'b484', 'cb2111c', 'c96111c', 'b480'], ['b483', 'b485', 'cb2112c', 'c96112c', 'b481'], ['cb2114t']]
    elif year > 2001 and year < 2013:
        coicop = ['11.1.1', '11.1.2', '11.1.3', '11.1.4.1', '11.1.4.2', '11.1.4.3', '11.1.4.4', '11.1.5', '11.1.6.1', '11.1.6.2',
                  '11.2.1', '11.2.2', '11.2.3']
        variables = [['cb1111t', 'cb1122t'], ['cb111ct', 'cb111dt', 'cb111et', 'cb111ft', 'cb111gt', 'cb111ht', 'cb111it', 'cb111jt'], 
                     ['cb1127t', 'cb1128t'], ['cb1115t', 'cb111ac', 'cb1116t', 'cb111bc', 'cb1125t', 'cb1126t'], ['cb1112t', 'cb1117c', 'cb1122t'],
                     ['cb1113t', 'cb1118c', 'cb1123t'], ['cb1114t', 'cb1119c', 'cb1124t'], ['cb112bt'], ['b260t'], ['cb1213t'],
                     ['b482', 'b484', 'cb2111c', 'c96111c', 'c96111w', 'b480'], ['b483', 'b485', 'cb2112c', 'c96112c', 'c96112w', 'b481'], ['cb2114t']]
    else:
        coicop = ['11.1.1', '11.1.2', '11.1.3', '11.1.4.1', '11.1.4.2', '11.1.4.3', '11.1.4.4', '11.1.5', '11.1.6.1', '11.1.6.2',
                  '11.2.1', '11.2.2', '11.2.3']
        variables = [['cb1111t', 'cb1122t'], ['cb111ct', 'cb111dt', 'cb111et', 'cb111ft', 'cb111gt', 'cb111ht', 'cb111it', 'cb111jt'], 
                     ['cb1127t', 'cb1128t'], ['cb1115t', 'cb111ac', 'cb1116t', 'cb111bc', 'cb1125t', 'cb1126t'], ['cb1112t', 'cb1117c', 'cb1122t'],
                     ['cb1113t', 'cb1118c', 'cb1123t'], ['cb1114t', 'cb1119c', 'cb1124t'], ['cb112bt'], ['b260t'], ['cb1213t'],
                     ['b482', 'b484', 'cb2111c', 'c96111c', 'c96111w'], ['b483', 'b485', 'cb2112c', 'c96112c', 'c96112w'], ['cb2114t']]
    
    for i in range(len(coicop)):
        useful_data[coicop[i]] = dvhh[variables[i]].sum(1)
    
    # 12
    coicop = ['12.1.1', '12.1.2', '12.1.3.1', '12.1.3.2', '12.1.3.3', '12.1.4', '12.1.5.1', '12.1.5.2', '12.1.5.3', '12.2.1.1',
              '12.2.1.2', '12.2.1.3', '12.2.2.1', '12.2.2.2', '12.2.2.3', '12.3.1.1', '12.3.1.2', '12.3.1.3', '12.3.1.4', '12.4.1.1',
              '12.4.1.2', '12.4.1.3', '12.4.2', '12.4.3.1', '12.4.3.2', '12.4.4', '12.5.1.1', '12.5.1.2', '12.5.1.3', '12.5.1.4',
              '12.5.1.5', '12.5.2.1', '12.5.2.2', '12.5.2.3', '12.5.3.1', '12.5.3.2', '12.5.3.3', '12.5.3.4', '12.5.3.5']
    variables = [['cc1111t'], ['cc1311t'], ['cc1312t'], ['cc1313t'], ['cc1314t'], ['cc1317t'], ['cc1315t'], ['cc1316t'], ['cc1211t'], ['cc3111t', 'cc3221t'],
                 ['cc3211t'], ['cc3224t'], ['cc3222t'], ['cc3223t'], ['cc3112t'], ['cc4111t'], ['cc4112t'], ['cc4121t'], ['cc4122t'], ['b110'],
                 ['b168'], ['cc5213c'], ['b229', 'cc5311c'], ['b188', 'cc5411c'], ['cc5412t'], ['cc5413t'], ['b273'], ['b280'], ['b281'], ['b282'],
                 ['b283'], ['b1802', 'cc6211c'], ['b238'], ['cc6214t'], ['cc7115t'], ['cc7111t', 'cc7112t'], ['cc7114t'], ['cc7116t'], ['cc7113t']]
    
    
    for i in range(len(coicop)):
        useful_data[coicop[i]] = dvhh[variables[i]].sum(1)
    
    # 13
    useful_data['13.1.1'] = (dvhh['b130']+dvhh['b150'])
    if year < 2010:
        useful_data['13.1.2'] = (dvhh['b208']+dvhh['b213'])
    else:
        useful_data['13.1.2'] = dvhh['b2081']
    useful_data['13.1.3'] = (dvhh['b030']+dvhh['b038p'])
    useful_data['13.2.1'] = dvhh['ck3111t']
    useful_data['13.2.2'] = dvhh['ck3112t']
    useful_data['13.2.3'] = (dvhh['b187']-dvhh['b179'])
    useful_data['13.3.1'] = dvhh['ck4111t']
    useful_data['13.3.2'] = dvhh['ck4112t']
    useful_data['13.4.1.1'] = (dvhh['ck5212t']+dvhh['ck5213t']+dvhh['ck5214t']+dvhh['ck5215t'])
    useful_data['13.4.1.2'] = dvhh['ck5216t']
    useful_data['13.4.2.1'] = (dvhh['ck5221t']+dvhh['ck5222t'])
    useful_data['13.4.2.2'] = dvhh['ck5223t']
    useful_data['13.4.2.3'] = (dvhh['b334h']+dvhh['ck5224c'])
    useful_data['13.4.2.4'] = dvhh['b265']
    useful_data['13.4.3.1'] = dvhh['ck5315c']
    useful_data['13.4.3.2'] = dvhh['b237']
    
    # 14
    if year < 2010:
        useful_data['14.1.1'] = (dvhh['b196']+dvhh['b197']+dvhh['b201']+dvhh['b202']+dvhh['b198']+dvhh['b199']+dvhh['cc5111c'])
    elif year == 2010:
        useful_data['14.1.1'] = (dvhh['b196']+dvhh['b197']+dvhh['b2011']+dvhh['b198']+dvhh['b199']+dvhh['cc5111c'])
    elif year > 2010 and year < 2013:
        useful_data['14.1.1'] = (dvhh['b2011']+dvhh['cc5111c'])
    elif year >= 2013 and year < 2018:
        useful_data['14.1.1'] = (dvhh['b1961']+dvhh['b2011']+dvhh['b1981']+dvhh['cc5111c'])
    else:
        useful_data['14.1.1'] = (dvhh['b1961']+dvhh['b2011']+dvhh['cc5111c'])
    
    useful_data['14.1.2'] = (dvhh['p071h']+dvhh['ck5116t'])
    useful_data['14.1.3'] = dvhh['b228']
    useful_data['14.2'] = (dvhh['b206']+dvhh['cc5511c']+dvhh['b205']+dvhh['cc5312c'])
    if year < 2006:
        useful_data['14.3.1'] = dvhh['p390']
    else:
        useful_data['14.3.1'] = dvhh['p390p']
    if year < 2006:
        useful_data['14.3.2'] = (dvhh['b387h']+dvhh['ck5411c'])
    else:
        useful_data['14.3.2'] = (dvhh['b387hp']+dvhh['ck5411c'])
    if year < 2006:
        useful_data['14.3.3'] = dvhh['b391h']
    else:
        useful_data['14.3.3'] = dvhh['b391hp']
    useful_data['14.3.4'] = dvhh['p068h']
    if year < 2006:
        useful_data['14.3.5'] = dvhh['p073h']
    else:
        useful_data['14.3.5'] = dvhh['p073hp']
    useful_data['14.3.6'] = dvhh['p391']*-1
    useful_data['14.3.7'] = dvhh['b390h']*-1
    if year < 2006:
        useful_data['14.4.1'] = (dvhh['p388']+dvhh['ck5412c'])
    else:
        useful_data['14.4.1'] = (dvhh['p388p']+dvhh['ck5412c'])
    if year < 2006:
        useful_data['14.4.2'] = dvhh['p029h']
    else:
        useful_data['14.4.2'] = dvhh['p029hp']
    useful_data['14.5.1'] = dvhh['ck1211t']
    if year < 2010:
        useful_data['14.5.2'] = (dvhh['b200']+dvhh['b203']-dvhh['b150'])
    elif year >= 2010 and year < 2013:
        useful_data['14.5.2'] = (dvhh['b200']+dvhh['b203']+dvhh['b204']-dvhh['b150'])
    else:
        useful_data['14.5.2'] = (dvhh['b200']+dvhh['b203']+dvhh['b204']-dvhh['b250'])
    useful_data['14.5.3'] = (dvhh['b101']+dvhh['b103'])
    useful_data['14.5.4'] = dvhh['ck1314t']
    useful_data['14.5.5'] = dvhh['b105']
    if year == 2001:
        useful_data['14.5.6'] = np.zeros(shape=np.size(dvhh,0))
    else:
        useful_data['14.5.6'] = dvhh['ck1316t']
    useful_data['14.5.7'] = dvhh['ck1315t']
    useful_data['14.5.8'] = dvhh['ck1411t']
    useful_data['14.6.1'] = dvhh['ck5111t']
    useful_data['14.6.2'] = dvhh['ck5113t']
    useful_data['14.6.3'] = dvhh['ck2111t']
    useful_data['14.7'] = dvhh['ck5316t']
    useful_data['14.8'] = (dvhh['c9431at']+dvhh['c9431bt']+dvhh['c9431ct']+dvhh['c9431dt']+dvhh['c9431et']+dvhh['c9431ft']+dvhh['c9431it'])
    
    return useful_data

