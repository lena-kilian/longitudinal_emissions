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

dv_list <-  c('Food_and_Drinks','Other_consumption', 'Recreation_culture_and_clothing',
              'Housing_water_and_waste', 'Electricity_gas_liquid_and_solid_fuels',
              'Private_and_public_road_transport', 'Air_transport', 'Total_ghg')

#for (dv in dv_list){
#  data[dv] <- data[dv] *10}

# make lists with variables
main_controls <- c('oac_1', 'oac_2', 'oac_3', 'oac_4', 'oac_5', 'oac_6', # 'oac_7',
                   'gor_1', 'gor_2', 'gor_3', 'gor_4', 'gor_5', 'gor_6', 'gor_7', 'gor_8', 
                   'gor_9', 'gor_10', 'gor_11', #'gor_12'
                   'hhld_income', 'year_before', 'relative_hhld', # 'hhld_oecd_equ',
                   #'fraction_female_adults', 'mean_age_adults'
                   'No_adult_male', 'No_adult_female')
no_people <- c('people_aged_m2', 'people_aged_2_4', 'people_aged_5_15', 'people_aged_16_17', 'people_aged_18_44', 
               'people_aged_45_59', 'people_aged_60_64', 'people_aged_65_69', 'people_aged_p69')
hhld_comp <- c('coh_1adult', 'coh_2adultswithchildren', 'coh_2padult18_30', 'coh_2adults', 'coh_1adultwithchildren',
               'coh_3padultswithchildren', 'coh_3padults', 'coh_1adultpensioner', 'coh_1adult18_30', 
               'coh_2padultspensioners') #, 'coh_Other',
hhld_age <- c('age_18_29', 'age_30_39', 'age_40_49',  'age_50_59',  'age_60_69', 'age_70p') # 'age_Householdwithchildren', 'age_Other'
students <- c('st_Allstudents') #, 'st_Notallstudents'

# run model with waist as the outcome and height as the covariate
make_formula <- function(dv, var_list){
  formula <- paste(dv, ' ~ ', sep='')
  for (var in main_controls){
    formula <- paste(formula, var, sep = ' + ')
    }
  for (dummy in var_list){
    formula <- paste(formula, dummy, paste(dummy, 'year_before', sep=':'), sep = ' + ')
  }
  formula
}

variable <- 'hhld_age'
if (variable == 'hhld_age') {
  data_mod <- filter(data, age != 'Other' & age != 'Household with children')
  var_list <- c('age_18_29', 'age_30_39', 'age_50_59',  'age_60_69', 'age_70p') # remove 40-49 one for dummy
}
if (variable != 'hhld_age') {
  data_mod <- data
  var_list <- eval(parse(text = variable))
}

dv <- 'Total_ghg'
data_mod['dv'] <- data_mod[dv] / data_mod['hhld_oecd_equ']
max <- mean(data_mod$dv) + (2.5*sd(data_mod$dv))
min <- mean(data_mod$dv) - (2.5*sd(data_mod$dv))
data_mod <- filter(data_mod, dv >= min & dv <= max)

# examine distribution of DV, which you have just simulated
qqnorm(data$Total_ghg); qqline(data$Total_ghg)

formula <- make_formula(dv, var_list)

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
  left_join(weights, by='id')

# weighted regression
mod_w <- mod <- lm(formula, data = data_w, weights=data_w$mod_weight)

# produce summary of model parameters
summary(mod_w) 
confint(mod_w)

# view diagnostic plots
par(mfrow = c(2, 2)); plot(mod_w); par(mfrow = c(1, 1))

residuals_w = data.frame(res = mod_w$residuals)
ggplot(data=residuals_w, aes(x=res)) + geom_histogram(binwidth=1) 
