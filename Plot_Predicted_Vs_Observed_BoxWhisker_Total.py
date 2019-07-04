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
Obs_data = r"C:\git\longfin_trawl_map\lfsmelt_2013_5mm_18mm_max_0.20grow\lfsmelt_2013_5mm_18mm_max_0.20grow\results\observed_total_abundance_quantiles.csv"
Pred_data = r"C:\git\longfin_trawl_map\lfsmelt_2013_5mm_18mm_max_0.20grow\lfsmelt_2013_5mm_18mm_max_0.20grow\results\predicted_total_abundance_quantiles.csv"
surveys = [1,2,3,4,5,6]
Obs_Label = 'Test_Observed'
Pred_Label = 'Test_Predicted'
 
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, title=Title)
lfp.make_TotalPredvsObs_BoxWhisker(Obs_data, Pred_data, Var, Log=False,  Obs_Label=Obs_Label, Pred_Label=Pred_Label)
