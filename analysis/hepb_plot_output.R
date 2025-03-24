library(data.table)
library(ggplot2)

# 95% CI
z <- 1.960
std <- function(x) sd(x)/sqrt(length(x))

load_r4py <- function(dir){
  files <- list.files(dir, pattern = "\\.csv$")
  
  tableList <- list()
  for (f in files){
    
    path <- paste0(dir, f)
    dt <- fread(path, fill=T)
    
    tableList[[f]] <- dt
  }
  dt <- rbindlist(tableList)  # Stack the list of tables into a single DT
  dt$model <- "repast4py"
  
  return(dt)
  
}

load_mason <- function(dir){
  files <- list.files(dir, pattern = "\\.csv$")
  
  colsToKeep <-  c("susceptible", "eclipse", "infected", "infecVirusLoad")
  
  tableList <- list()
  for (f in files){
    
    path <- paste0(dir, f)
    dt <-  fread(path, select=colsToKeep, fill=T)
    dt$run <- 0
    dt$tick <- seq(1,1351)
    
    tableList[[f]] <- dt
  }
  dt <- rbindlist(tableList)  # Stack the list of tables into a single DT
  dt$model <- "mason"
  
  dt[, `viral load (log)` := log10(infecVirusLoad)]
  dt$infecVirusLoad <- NULL
  
  setnames(dt, old = c('eclipse'), 
           new = c('eclipsed'))
  
  return(dt)
  
}

mason_dir <- "L:\\HepCEP\\HepBV\\HepBV\\output\\"
r4py_dir <- "L:\\HepCEP\\hepbport\\local_proj\\output\\"

r4py_dt <- load_r4py(r4py_dir)
mason_dt <- load_mason(mason_dir)

dt <- rbind(r4py_dt, mason_dt)

# Calculate the mean and std of yearly incidence rate
susc <- dt[, list(mean=mean(susceptible), std=std(susceptible)), 
                                  by=list(tick, model)]
ecli <- dt[, list(mean=mean(eclipsed), std=std(eclipsed)), 
           by=list(tick, model)]

infe <- dt[, list(mean=mean(infected), std=std(infected)), 
               by=list(tick, model)]

viral_load <- dt[, list(mean=mean(`viral load (log)`), std=std(`viral load (log)`)), 
           by=list(tick, model)]

# Color Version
p <- ggplot(ecli) + 
  geom_line(aes(x=tick/24, y=mean, color=model), size=1) +

  geom_ribbon(aes(x=tick/24, ymin=mean-z*std, ymax=mean+z*std, fill=model),alpha=0.3,colour=NA) +

  scale_y_continuous(limits = c(0, 3.01E5), breaks = seq(0, 3E5, 1E5)) +
  scale_x_continuous(limits = c(0, 56), breaks = seq(0, 56, 7)) +
   
  labs(y="Cell Count", x="Day", color="model") +  
  #labs(y="Viral Load Log10", x="Day", color="model") + 
  theme_bw() +
  #  theme_minimal() + 
  theme(text = element_text(size=22), 
        legend.position = c(.75, .25), 
        legend.text=element_text(size=22),
        legend.background = element_rect(fill="white", size=0.5, linetype="solid", colour ="gray")) +
  theme(axis.text=element_text(size=22),axis.title=element_text(size=22)) +
  
  guides(color=guide_legend(title="model"),fill=guide_legend(title="model"))

show(p)
ggsave(paste0(mason_dir,"Eclipsed Count.png"), plot=p, width=10, height=8)

