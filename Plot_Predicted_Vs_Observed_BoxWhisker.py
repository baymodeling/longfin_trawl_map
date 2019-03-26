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
Pred_data_dir = r"C:\git\longfin_trawl_map\hatching_fit_multiple_cohorts"
Obs_data_dir = r"C:\git\longfin_trawl_map\SLS"
Pred_data = ["quantiles_1.csv",
             "quantiles_2.csv",
             "quantiles_3.csv",
             "quantiles_4.csv",
             "quantiles_5.csv",
             "quantiles_6.csv"]
Obs_data = ['SLS_quantiles_4mm-8mm_2012-12-21_grow0.20_2013.csv', 
            'SLS_quantiles_4mm-8mm_2013-01-03_grow0.20_2013.csv',
            "SLS_quantiles_4mm-8mm_2013-01-15_grow0.20_2013.csv",
            "SLS_quantiles_4mm-8mm_2013-01-29_grow0.20_2013.csv",
            "SLS_quantiles_4mm-8mm_2013-02-12_grow0.20_2013.csv",
            "SLS_quantiles_4mm-8mm_2013-02-26_grow0.20_2013.csv"]
Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
sizes = [4,8]
surveys = [1,2,3,4,5,6]
 
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_PredvsObs_BoxWhisker(Obs_data_dir, Pred_data_dir, Obs_data, Pred_data, Chron_data, Var, Log=True)