'''
Created on Mar 26, 2019

@author: scott
'''

from Longfin_Plotter import LongfinPlotter
import os


run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

runs = {
        'Run1':{'Predicted_Data_Dir': r"C:\git\longfin_trawl_map\hatching_fit_multiple_cohorts",
                'Predicted_Data': ["quantiles_1.csv",
                                   "quantiles_2.csv",
                                   "quantiles_3.csv",
                                   "quantiles_4.csv",
                                   "quantiles_5.csv",
                                   "quantiles_6.csv"],
                'Year': 2012,
                'Sizes': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"],
                'Surveys': [1,2,3,4,5,6],
                'Observed_Data': r"C:\git\longfin_trawl_map\Total_abun\SLS_quantiles_3mm-11mm_2013.csv",
                'Var': 'Abundance',
                'Chron_data': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"],
                'Log':True},
        
        'Run2': {'Predicted_Data_Dir': r"C:\git\longfin_trawl_map\hatching_fit_multiple_cohorts",
                'Predicted_Data': ["quantiles_1.csv",
                                   "quantiles_2.csv",
                                   "quantiles_3.csv",
                                   "quantiles_4.csv",
                                   "quantiles_5.csv",
                                   "quantiles_6.csv"],
                'Year': 2012,
                'Sizes': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"],
                'Surveys': [1,2,3,4,5,6],
                'Observed_Data': r"C:\git\longfin_trawl_map\Total_abun\SLS_quantiles_3mm-11mm_2013.csv",
                'Var': 'Abundance',
                'Chron_data': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"],
                'Log':False},
        }

for run in runs.keys():
    print 'Plotting', run
    lfp = LongfinPlotter(run_dir, grd_file, runs[run]['Year'], runs[run]['Sizes'], runs[run]['Surveys'])
    lfp.make_TotalPredvsObs_BoxWhisker(runs[run]['Predicted_Data_Dir'], runs[run]['Predicted_Data'], runs[run]['Observed_Data'],
                                       runs[run]['Chron_data'], runs[run]['Var'], Log=runs[run]['Log'])