'''
Created on Mar 26, 2019

@author: scott
'''

from Longfin_Plotter import LongfinPlotter
import os

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')
year = 2013
Var = 'Abundance'
Title = 'Test Run'
Obs_data = r"C:\git\longfin_trawl_map\lfsmelt_2013_5mm_18mm_max_0.20grow\lfsmelt_2013_5mm_18mm_max_0.20grow\results\observed_cohort_abundance_quantiles.csv"
Pred_data = r"C:\git\longfin_trawl_map\lfsmelt_2013_5mm_18mm_max_0.20grow\lfsmelt_2013_5mm_18mm_max_0.20grow\results\predicted_cohort_abundance_quantiles.csv"
Obs_Label = 'Test_Observed'
Pred_Label = 'Test_Predicted'
output_directory = r'Test_Directory'
fishtype = 'Delta Smelt'
surveys = [1,2,3,4,5,6]
cohorts = [1,2,3,4,5,6]
 
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, cohorts=cohorts, title=Title,output_directory=output_directory)
lfp.make_PredvsObs_BoxWhisker(Obs_data, Pred_data, Var, Log=False, Obs_Label=Obs_Label, Pred_Label=Pred_Label, Fishtype=fishtype)