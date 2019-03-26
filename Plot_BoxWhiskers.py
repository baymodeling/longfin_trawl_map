'''
Created on Mar 26, 2019

@author: scott
'''

from Longfin_Plotter import LongfinPlotter
import os

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

runs = {
        'Run1':{'Trawl_data': [r"J:\Longfin\bar_plots\SLS_quantiles_12mm-16mm_2012-3-1_grow0.30_2012.csv", 
                               r"J:\Longfin\from_Ed\20mm_quantiles_12mm-16mm_2012-3-1_grow0.20_2012.csv"],
                'Year': 2012,
                'Sizes': [12,16],
                'Surveys': [[1,2,3,4,5,6], [1,2,3,4,5,6,7,8,9]],
                'Var': 'Abundance',
                'Chronological': True,
                'Chron_data': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", 
                               r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"],
                'Log':True},
        
        'Run2': {'Trawl_data': [r"J:\Longfin\bar_plots\SLS_quantiles_12mm-16mm_2013-3-1_grow0.30_2013.csv", 
                               r"J:\Longfin\from_Ed\20mm_quantiles_12mm-16mm_2013-3-1_grow0.20_2013.csv"],
                'Year': 2013,
                'Sizes': [10,16],
                'Surveys': [[1,2,3,4,5,6], [1,2,3,4,5,6,7,8,9]],
                'Var': 'Abundance',
                'Chronological': True,
                'Chron_data': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", 
                               r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"],
                'Log':True}
        }

for run in runs.keys():
    print 'Plotting', run
    lfp = LongfinPlotter(run_dir, grd_file, runs[run]['Year'], runs[run]['Sizes'], runs[run]['Surveys'])
    lfp.make_BoxWhisker(runs[run]['Trawl_data'], runs[run]['Var'], Chronological=runs[run]['Chronological'],
                        Chronological_data=runs[run]['Chron_data'], Log=runs[run]['Log'])