library(tidyverse)


setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis/")

all_data <- read_csv('data/processed/GHG_Estimates_LCFS/Regression_data.csv') %>%
  mutate(year_str = paste('Year', year, sep=' '))

data <- all_data %>% 
  gather(Product, ghg, c(`Food and Drinks`, `Other consumption`, `Recreation, culture, and clothing`, `Housing, water and waste`, `Electricity, gas, liquid and solid fuels`,
                         `Private and public road transport`, `Air transport`, Total)) %>%
  mutate(ghg = ifelse(ghg < 0, 0, ghg),
         ln_income = log(`income anonymised` + 0.001),
         ln_ghg = log(ghg + 0.001))

data %>% 
  ggplot(aes(x=ln_income, y=ln_ghg, linetype=year_str, color=Product)) +
  geom_smooth(method=lm)


results <- data.frame()
product_list <- distinct(select(data, Product))$Product
for (item in c('income_group', 'composition of household', 'age_group', 'student_hhld')){
  for (pt in product_list){
    for (yr in c(2007, 2009)){
      temp <- data
      temp['group'] <- temp[item]
      group_list <- distinct(select(temp, group))$group
      temp2 <- temp %>% filter(Product == pt & year == yr)
      temp3 <- data.frame(group_var = item, group = 'All households', product = pt, year = yr, elasticity = lm(ln_ghg ~ ln_income, data = temp2)$coefficients['ln_income'])
      results <- results %>% rbind(temp3)
      for (gp in group_list){
        temp2 <- temp %>% filter(Product == pt & year == yr & group == gp)
        temp3 <- data.frame(group_var = item, group = gp, product = pt, year = yr, elasticity = lm(ln_ghg ~ ln_income, data = temp2)$coefficients['ln_income'])
        results <- results %>% rbind(temp3)
      }
    }
  }
}


results %>% write_csv('data/processed/GHG_Estimates_LCFS/Elasticity_regression_results.csv')

for (item in c('income_group', 'composition of household', 'age_group', 'student_hhld')){
  results %>% 
    mutate(year_str = paste('Year', year, sep=' ')) %>% 
    filter(group_var == item)  %>% 
    ggplot(aes(x=product, y=elasticity, color=group, shape=year_str)) +
    geom_point()
}