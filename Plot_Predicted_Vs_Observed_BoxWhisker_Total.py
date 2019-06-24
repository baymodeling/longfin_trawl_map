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
Obs_data = r"C:\git\longfin_trawl_map\5-28-2019\observed_total_abundance_quantiles.csv"
Pred_data = r"C:\git\longfin_trawl_map\new_predicted_06132019\results\results\predicted_total_abundance_quantiles.csv"
Chron_data = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
sizes = [6,9]
surveys = [1,2,3,4,5,6]
 
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
lfp.make_TotalPredvsObs_BoxWhisker(Obs_data, Pred_data, Chron_data, Var, Log=False)