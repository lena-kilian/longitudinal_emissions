library(ggridges)
library(tidyverse)
library(purrr)
library(tm)

setwd("~/Documents/Ausbildung/UoLeeds/PhD/Analysis")

# import data
first_year = 2001
last_year = 2019

hhd_ghg <- read_csv(paste('data/processed/GHG_Estimates_LCFS/Household_emissions_', first_year, '.csv', sep='')) %>%
  select(`no people`, `no people weighted`, new_desc, c('1.1.1.1':'12.5.3.5')) %>%
  mutate(year = first_year)

for (i in seq(first_year + 1, last_year)){
  temp <- read_csv(paste('data/processed/GHG_Estimates_LCFS/Household_emissions_', i, '.csv', sep='')) %>%
    select(`no people`, `no people weighted`, new_desc, c('1.1.1.1':'12.5.3.5')) %>%
    mutate(year = i)
  hhd_ghg <- hhd_ghg %>% rbind(temp)
}

hhd_ghg <- hhd_ghg %>%
  mutate(total_ghg = select(hhd_ghg, c('1.1.1.1':'12.5.3.5')) %>% rowSums()) %>%
  select(`no people`, `no people weighted`, new_desc, year, total_ghg) %>%
  mutate(ghg_pc = total_ghg / `no people weighted`) %>%
  drop_na() %>%
  arrange(ghg_pc)

# Separate income
# income plot
data <- hhd_ghg %>% 
  drop_na() %>%
  filter(year >= 2007) %>%
  filter(year <= 2009)
data$year_str = factor(data$year, levels=c(2009, 2008, 2007))
  

order <- data %>% 
  mutate(avg_ghg = ghg_pc) %>% 
  group_by(new_desc) %>% 
  summarise(across(avg_ghg, median)) %>%
  distinct() %>%
  arrange(avg_ghg)
order$order = factor(order$new_desc, levels=order$new_desc)

data <- data %>%
  left_join(order, by='new_desc') 

ggplot() +
  geom_density_ridges(data=data, aes(y=order, x=ghg_pc, colour=year_str), alpha = 0, scale=1) +  # scale = 0.8,
  xlim(-5, 40)

ggplot() +
  geom_boxplot(data=data, aes(y=order, x=ghg_pc, fill=year_str)) + # "#F1B593" "#C54A43"
  xlim(0, 200)




  scale_y_discrete(limits = rev(levels(temp$transport_f))) + #, position = "right") + 
  guides(fill = guide_legend(override.aes = list(shape = 16))) +
  ylab('') +
  xlab(' ') +
  xlim(-18, 13) +
  theme_classic() +
  #facet_grid(transport_f ~ predictors_f, scale="free") +
  geom_vline(xintercept=c(0,0), linetype="dotted") +
  coord_cartesian(xlim = c(-4, 13), clip = "off") + 
  # add global coef.
  geom_point(data = global_coef_fig, aes(y=transport_f, x=global_coef, fill=global_pval_f),
             colour="black", pch=21, size = 5, inherit.aes = FALSE) +
  scale_fill_manual(values=colour$pval_cols, name='Global coef.') +
  #geom_text(aes(x=-1.6*4, y=labels$transport_f, label=labels$AIC), 
  #          colour="black", size=9, family="Times New Roman") +
  #geom_text(aes(x=-3*4, y=labels$transport_f, label=labels$transport_f), 
  #          colour="black", size=9, family="Times New Roman", hjust = 0) +
  theme(text = element_text(colour="black", size=30, family="Times New Roman"),
        plot.margin = unit(c(0, 0, 0, 0), "lines"))
ggsave('Longitudinal_Emissions/outputs/Ridges/ridges_incomeonly.png')