# regression analysis to investigate impact of gender

rm(list=ls())

library(tidyverse)
library(lmtest)
library(MASS)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis")

#################
## 2002 - 2009 ##
#################

data <- read_csv('data/processed/Longitudinal_model/model_data_2007-09.csv') %>%
  filter(oac != 'oac_')

dv_list <-  c('Food_and_Drinks', 'Other_consumption', 'Recreation_culture_and_clothing',
              'Housing_water_and_waste', 'Electricity_gas_liquid_and_solid_fuels',
              'Private_and_public_road_transport', 'Air_transport', 'Total_ghg')

#for (dv in dv_list){
#  data[dv] <- data[dv] *10}

# make lists with variables
main_controls <- c('oac_1', 'oac_2', 'oac_3', 'oac_4', 'oac_5', 'oac_6', # 'oac_7',
                   'gor_1', 'gor_2', 'gor_3', 'gor_4', 'gor_5', 'gor_6', 'gor_7', 'gor_8', 
                   'gor_9', 'gor_10', 'gor_11', #'gor_12'
                   'hhld_income', 'year_before', 'relative_hhld', 'partner_hhld', # 'hhld_oecd_equ',
                   #'fraction_female_adults', 'mean_age_adults', 'mean_age_children'
                   'mean_age_adults', 'hhld_oecd_equ', 'fraction_female')
no_people <- c('people_aged_m2', 'people_aged_2_4', 'people_aged_5_15', 'people_aged_16_17', 'people_aged_18_44', 
               'people_aged_45_59', 'people_aged_60_64', 'people_aged_65_69', 'people_aged_p69')
hhld_comp <- c('coh_1adult', 'coh_2adultswithchildren', 'coh_2padult18_30', 'coh_2adults', 'coh_1adultwithchildren',
               'coh_3padultswithchildren', 'coh_3padults', 'coh_1adultpensioner', 'coh_1adult18_30', 
               'coh_2padultspensioners') #, 'coh_Other'
hhld_age <- c('age_18_29', 'age_30_39', 'age_40_49',  'age_50_59',  'age_60_69', 'age_70p') # 'age_Householdwithchildren', 'age_Other'
students <- c('st_Allstudents') #, 'st_Notallstudents'
ses <- c("st_09_Routineoccupations", "st_04_Intermediateadministrativeserviceandtechnicaloccupations", 
         "st_07_Semi_routineoccupations", "st_00_Higherprofessionalandmanagerial", "st_02_Lowerprofessionalandmanagerialandhighertechnical",
         "st_06_Lowersupervisoryandtechnicaloccupations", "st_01_Employers", "st_08_Full_timestudents", 
         "st_03_Highersupervisory", "st_05_Ownaccountworkers") # , "st_10_Unemployed"

# run model with waist as the outcome and height as the covariate
make_formula <- function(var_list){
  formula <- paste('dv ~ ', sep='')
  for (var in main_controls){
    formula <- paste(formula, var, sep = ' + ')
    }
  for (dummy in var_list){
    formula <- paste(formula, dummy, paste(dummy, 'year_before', sep=':'), sep = ' + ')
  }
  formula
}

variable <- 'hhld_comp'
if (variable == 'hhld_comp') {
  data_mod <- filter(data, coh != 'Other')
  var_list <- c('coh_2adultswithchildren', 'coh_2padult18_30', 'coh_2adults', 'coh_1adultwithchildren',
                'coh_3padultswithchildren', 'coh_3padults', 'coh_1adultpensioner', 'coh_1adult18_30', 
                'coh_2padultspensioners') # remove 'coh_1adult' one for dummy
}
if (variable != 'hhld_comp') {
  data_mod <- data
  var_list <- eval(parse(text = variable))
}

for (dv in dv_list){
  # winsorise at 10%
  data_mod <- data
  data_mod['winsorise'] <- data_mod[dv] / data_mod['hhld_oecd_equ']
  data_mod['dv'] <- data_mod[dv]
  minmax <- quantile(data_mod$winsorise, probs = c(0, 0.9), na.rm = FALSE)
  max <- minmax[2]
  min <- minmax[1]
  data_mod <- data_mod %>%
    mutate(dv = ifelse(winsorise < minmax[1], dv * hhld_oecd_equ, dv),
           dv = ifelse(winsorise > minmax[2], dv * hhld_oecd_equ, dv))
           
  data_mod <- data_mod %>%
    dplyr::select(c('dv', dv_list, main_controls, 'oac_7', 'gor_12', eval(parse(text = variable)))) %>%
    drop_na()
    
  # examine distribution of DV, which you have just simulated
  qqnorm(data$Total_ghg); qqline(data$Total_ghg)
  
  formula <- make_formula(var_list) #formula <- gsub(' + year_before', '', formula)
  
  mod <- lm(formula, data = data_mod) 
  
  # produce summary of model parameters
  summary(mod)
  confint(mod)
  
  # plot resdisuals
  residuals = data.frame(res = mod$residuals)
  ggplot(data=residuals, aes(x=res)) + geom_histogram(binwidth=1) 
  
  # view diagnostic plots
  par(mfrow = c(2, 2)); plot(mod); par(mfrow = c(1, 1))
  
  
  
  ## WEIGHTED REGRESSION ##
  # create weights
  data_w <- data_mod  %>% mutate(id = 1:nrow(data_mod))
  
  residuals <- data.frame(res = mod$residuals, id=data_w$id) %>% 
    arrange(res) %>%
    mutate(group = rep(1:(nrow(data_w)/10), each = 10)[1:nrow(data_w)])
  
  weights <- data.frame(mod_weight = c(0), group = c(0))
  for (i in 1:(nrow(data_w)/10)){
    temp <- residuals %>% filter(group == i) %>% dplyr::select(res) %>% var()
    weights <- rbind(weights, data.frame(mod_weight = c(temp), group = c(i)))
    }
  
  weights <- residuals %>% 
    left_join(filter(weights, group!=0), by='group') %>% 
    dplyr::select(c(id, mod_weight)) %>%
    mutate(mod_weight = 1 / mod_weight)
  
  data_w <- data_w %>%
    left_join(weights, by='id') %>%
    drop_na()
  
  # repeat to get fitted values
  mod_2 <- lm(formula, data = data_w) 
  par(mfrow = c(2, 2)); plot(mod_2); par(mfrow = c(1, 1)) # view diagnostic plots
  #jpeg(paste('Longitudinal_Emissions/outputs/Regression/Regression_residuals/', dv, '_hhdcomp.jpeg', sep=''), quality = 100)
  
  results_2 <- data.frame(summary(mod_2)$coefficients)
  results_2['variable'] <- row.names(results_2)
  temp <- data.frame(confint(mod_2))
  temp['variable'] <- row.names(temp)
  results_2 <- left_join(results_2, temp, by=c('variable'))
  results_2['R2'] <- summary(mod_2)$r.squared
  results_2['adjR2'] <- summary(mod_2)$adj.r.squared
  results_2['F'] <- summary(mod_2)$fstatistic[1]
  results_2['n_var'] <- summary(mod_2)$fstatistic[2]
  results_2['df'] <- summary(mod_2)$fstatistic[3]
  results_2['p'] <- pf(summary(mod_2)$fstatistic[1], summary(mod_2)$fstatistic[2], summary(mod_2)$fstatistic[3], 
                       lower.tail = F) 
  results_2['weighted'] <- FALSE
  
  # weighted regression
  mod_w <- lm(formula, data = data_w, weights=data_w$mod_weight)
  par(mfrow = c(2, 2)); plot(mod_w); par(mfrow = c(1, 1)) # view diagnostic plots
  #jpeg(paste('Longitudinal_Emissions/outputs/Regression/Regression_residuals/', dv, '_W.jpeg', sep=''), quality = 100)
  
  mod_2 <- lm(formula, data = data_w) 
  par(mfrow = c(2, 2)); plot(mod_2); par(mfrow = c(1, 1)) # view diagnostic plots
  #jpeg(paste('Longitudinal_Emissions/outputs/Regression/Regression_residuals/', dv, '_hhdcomp.jpeg', sep=''), quality = 100)
  
  # produce summary of model parameters
  results_w <- data.frame(summary(mod_w)$coefficients)
  results_w['variable'] <- row.names(results_w)
  temp <- data.frame(confint(mod_w))
  temp['variable'] <- row.names(temp)
  results_w <- left_join(results_w, temp, by=c('variable'))
  results_w['R2'] <- summary(mod_w)$r.squared
  results_w['adjR2'] <- summary(mod_w)$adj.r.squared
  results_w['F'] <- summary(mod_w)$fstatistic[1]
  results_w['n_var'] <- summary(mod_w)$fstatistic[2]
  results_w['df'] <- summary(mod_w)$fstatistic[3]
  results_w['p'] <- pf(summary(mod_w)$fstatistic[1], summary(mod_w)$fstatistic[2], summary(mod_w)$fstatistic[3], 
                       lower.tail = F) 
  results_w['weighted'] <- TRUE
  
  results_2 %>% 
    rbind(results_w) %>%
    write_csv(paste('Longitudinal_Emissions/outputs/Regression/Regression_', dv, '_hhdcomp.csv', sep=''))
  
  # plot residuals
  residuals_w = data.frame(res = mod_w$residuals)
  ggplot(data=residuals_w, aes(x=res)) + geom_histogram(binwidth=1) 
  
  
  # plot og y and fitted ys
  y_fitted <- data_w %>%
    dplyr::select(dv) %>%
    mutate(y_mod = fitted(mod_2),
           y_mod_w = fitted(mod_w))
  
  #ggplot(data=y_fitted) + 
  #  geom_point(aes(x=dv, y=y_mod), color='red') +
  #  geom_point(aes(x=dv, y=y_mod_w), color='blue') +
  #  geom_point(aes(x=y_mod, y=y_mod_w), color='green') +
  #  xlim(0, 50) +
  #  ylim(0, 50)
  
  # save data and outputs
  data_w %>% 
    gather(age_group, age_dummy, eval(parse(text = variable))) %>%
    filter(age_dummy == 1) %>% 
    write_csv(paste('Longitudinal_Emissions/outputs/Data_W_from_R_', dv, '_hhdcomp.csv', sep=''))
}

