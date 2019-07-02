'''
Created on Jul 2, 2019

@author: scott
@organization: Resource Management Associates
@contact: scott@rmanet.com
@note:
'''
from Longfin_Plotter import LongfinPlotter
import os


data_dir = r"C:\git\longfin_trawl_map\lfsmelt_2013_5mm_18mm_max_0.20grow\lfsmelt_2013_5mm_18mm_max_0.20grow\results"

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')
year = 2013

surveys = [1,2,3,4,5,6]
cohorts = [1,2,3,4,5,6]

#plot pred vs obs
Var = 'Abundance'
Obs_data = os.path.join(data_dir, "observed_cohort_abundance_quantiles.csv")
Pred_data = os.path.join(data_dir, "predicted_cohort_abundance_quantiles.csv")
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, cohorts=cohorts)
lfp.make_PredvsObs_BoxWhisker(Obs_data, Pred_data, Var, Log=False)



#Plot Entrainment
Var = 'Larvae'
Pred_Entrainment_data = os.path.join(data_dir, "predicted_cohort_source_entrainment_quantiles.csv")
max = 20000000.
lfp = LongfinPlotter(run_dir, grd_file, year, cohorts=cohorts)
lfp.make_BoxWhisker(Pred_Entrainment_data, Var, datatype='entrainment', Log=False, max=max)

#plot regional hatch
Pred_hatch_data = os.path.join(data_dir, "cohort_hatch_quantiles.csv")
max=5000000000.
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, cohorts=cohorts)
lfp.make_BoxWhisker(Pred_hatch_data, Var, datatype='hatch', Log=False, max=max)


#total Plots
Var = 'Abundance'
Obs_total_data = os.path.join(data_dir, "observed_total_abundance_quantiles.csv")
Pred_total_data = os.path.join(data_dir, "predicted_total_abundance_quantiles.csv")
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys)
lfp.make_TotalPredvsObs_BoxWhisker(Obs_total_data, Pred_total_data, Var, Log=False)
