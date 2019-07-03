'''
Created on Jul 3, 2019

@author: scott
@organization: Resource Management Associates
@contact: scott@rmanet.com
@note:
'''

from Longfin_Plotter import LongfinPlotter
import os


scenario_1 = r"C:\git\longfin_trawl_map\lfsmelt_2013_5mm_18mm_max_0.20grow\lfsmelt_2013_5mm_18mm_max_0.20grow\results"
scenario_2 = r"C:\git\longfin_trawl_map\lfsmelt_2013_5mm_18mm_max_0.20grow\lfsmelt_2013_5mm_18mm_max_0.20grow\results"

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')
year = 2013

surveys = [1,2,3,4,5,6]
cohorts = [1,2,3,4,5,6]

#comparisopn plot
Var = 'Abundance'
Obs_data = os.path.join(scenario_1, "observed_cohort_abundance_quantiles.csv")
Pred_data = [os.path.join(scenario_1,'predicted_cohort_abundance_quantiles.csv'),
             os.path.join(scenario_2,'predicted_cohort_abundance_quantiles.csv')]
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, cohorts=cohorts)
lfp.make_MultiPredvsObs_BoxWhisker(Obs_data, Pred_data, Var, Log=False)

#plot pred vs obs scenario 1
Var = 'Abundance'
Obs_data = os.path.join(scenario_1, "observed_cohort_abundance_quantiles.csv")
Pred_data = os.path.join(scenario_1, "predicted_cohort_abundance_quantiles.csv")
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, cohorts=cohorts)
lfp.make_PredvsObs_BoxWhisker(Obs_data, Pred_data, Var, Log=False)

#plot pred vs obs scenario 1
Var = 'Abundance'
Obs_data = os.path.join(scenario_2, "observed_cohort_abundance_quantiles.csv")
Pred_data = os.path.join(scenario_2, "predicted_cohort_abundance_quantiles.csv")
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, cohorts=cohorts)
lfp.make_PredvsObs_BoxWhisker(Obs_data, Pred_data, Var, Log=False)