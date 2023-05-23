# estimate income elasticities

rm(list=ls())

library(tidyverse)

wd <- rstudioapi::getSourceEditorContext()$path
setwd(paste(strsplit(wd,'Analysis')[[1]][1], 'Analysis/', sep=''))

all_data <- read_csv('data/processed/GHG_Estimates_LCFS/Regression_data.csv')

data <- all_data %>% 
  gather(Product, ghg, c(`Food and Drinks`, `Other consumption`, `Recreation, culture, and clothing`, `Housing, water and waste`, 
                         `Electricity, gas, liquid and solid fuels`, `Private and public road transport`, `Air transport`, Total)) %>%
  mutate(ghg = ifelse(ghg < 0, 0, ghg),
         ln_income = log(`income anonymised` + 0.001),
         ln_ghg = log(ghg + 0.001))

results <- data.frame()
product_list <- distinct(dplyr::select(data, Product))$Product
for (item in c('all', 'age_group_hrp', 'income_group')){
  for (pt in product_list){
    for (cpi in c('cpi', 'regular')){
      # add results by year
      for (yr in seq(2001, 2020)){
        yr_str = paste('Year', yr, sep='_')
        temp <- data
        temp['group'] <- temp[item]
        temp2 <- temp %>% 
          filter(Product == pt & year == yr_str & cpi == cpi) %>%
          mutate(group = ifelse(group == '0', 'NA', group))
        group_list <- distinct(dplyr::select(temp2, group))$group
        for (gp in group_list){
          temp4 <- temp2 %>% filter(group == gp)
          mod <- lm(ln_ghg ~ ln_income, data = temp4)
          temp3 <- data.frame(group_var = item, group = gp, product = pt, year = yr, cpi=cpi,
                              elasticity = mod$coefficients['ln_income'], ci_low = confint(mod)[2], ci_up = confint(mod)[4])
          results <- results %>% rbind(temp3)
        } # close group
      } # close year
      # add result for all years combined
      temp <- data
      temp['group'] <- temp[item]
      temp2 <- temp %>% 
        filter(Product == pt & cpi == cpi) %>%
        mutate(group = ifelse(group == '0', 'NA', group))
      group_list <- distinct(dplyr::select(temp2, group))$group
      for (gp in group_list){
        temp4 <- temp2 %>% filter(group == gp)
        mod <- lm(ln_ghg ~ ln_income, data = temp4)
        temp3 <- data.frame(group_var = item, group = gp, product = pt, year = 'all', cpi=cpi,
                            elasticity = mod$coefficients['ln_income'], ci_low = confint(mod)[2], ci_up = confint(mod)[4])
        results <- results %>% rbind(temp3)
      } # close group
    } # close cpi
  } # close product
} # close item


results %>% write_csv('data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')
