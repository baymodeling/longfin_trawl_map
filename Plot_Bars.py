'''
Created on Mar 26, 2019

@author: scott
'''

from Longfin_Plotter import LongfinPlotter
import os

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

runs = {
        'Run1':{'Trawl_data': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", 
                               r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"],
                'Year': 2013,
                'Sizes': [6,10],
                'Surveys': [[3,4,5,6], [1,2,3,4,5,6,7,8,9]],
                'Var': 'Abundance',
                'StaticVols': r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv",
                'GrowthRate': 0.2,
                'Chronological': True,
                'Log':True},
        
        'Run2': {'Trawl_data': [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", 
                                r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"],
                'Year': 2014,
                'Sizes': [6,10],
                'Surveys': [[3,4,5,6], [1,2,3,4,5,6,7,8,9]],
                'Var': 'Abundance',
                'StaticVols': r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv",
                'GrowthRate': 0.2,
                'Chronological': True,
                'Log':True}
        }

for run in runs.keys():
    print 'Plotting', run
    lfp = LongfinPlotter(run_dir, grd_file, runs[run]['Year'], runs[run]['Sizes'], runs[run]['Surveys'])
    lfp.make_Bars(runs[run]['Trawl_data'],runs[run]['StaticVols'], runs[run]['Var'], GrowthRate=runs[run]['GrowthRate'], 
                  Chronological=runs[run]['Chronological'], Log=runs[run]['Log'])