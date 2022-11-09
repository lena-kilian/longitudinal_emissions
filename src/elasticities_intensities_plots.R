# estimate income elasticities

rm(list=ls())

library(tidyverse)
library(ggridges)


setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis/")

all_data <- read_csv('data/processed/GHG_Estimates_LCFS/Elasticity_regression_results_with_intensities.csv')


# age 

data_plot <- filter(all_data, year != 'all' & cpi != 'cpi' & group != 'Other' & product == 'Total' & group_var=='age_group_hrp')
ggplot(data_plot, aes(y=group, x=elasticity)) +
  geom_density_ridges2(alpha=1)

data_plot <- filter(all_data, year != 'all' & cpi != 'cpi' & group != 'Other' & product != 'Total' & group_var=='age_group_hrp')
ggplot(data_plot, aes(fill=group, x=elasticity, y=product)) +
  geom_density_ridges2(alpha=0.7)

# income

data_plot <- filter(all_data, year != 'all' & cpi != 'cpi' & group != 'Other' & product == 'Total' & group_var=='income_group')
ggplot(data_plot, aes(y=group, x=elasticity)) +
  geom_density_ridges2(alpha=1)

data_plot <- filter(all_data, year != 'all' & cpi != 'cpi' & group != 'Other' & product != 'Total' & group_var=='income_group')
ggplot(data_plot, aes(fill=group, x=elasticity, y=product)) +
  geom_density_ridges2(alpha=0.7)

# all households
data_plot <- filter(all_data, year != 'all' & cpi != 'cpi' & group != 'Other' & product == 'Total' & group=='all_households')
ggplot(data_plot, aes(y=group, x=elasticity)) +
  geom_density_ridges2(alpha=1)

data_plot <- filter(all_data, year != 'all' & cpi != 'cpi' & group != 'Other' & product != 'Total' & group=='all_households')
ggplot(data_plot, aes(fill=group, x=elasticity, y=product)) +
  geom_density_ridges2(alpha=0.7)

# all years

data_plot <- filter(all_data, year == 'all' & cpi != 'cpi' & group == 'all_households' & group_var=='income_group')
ggplot(data_plot, aes(y=product, x=elasticity)) +
  geom_density_ridges2(alpha=1)

data_plot <- filter(all_data, year == 'all' & cpi != 'cpi' & group != 'Other' & group_var=='age_group_hrp')
ggplot(data_plot, aes(y=product, x=elasticity)) +
  geom_density_ridges2(alpha=1)


