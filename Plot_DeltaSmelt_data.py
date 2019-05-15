'''
Created on May 14, 2019

@author: scott
'''
import os
import datetime as dt
from Longfin_Plotter import LongfinPlotter

obs_data = r"C:\git\longfin_trawl_map\5-10-2019\20mm_survey_summary_deltasmelt.csv"
datafile = r"C:\git\longfin_trawl_map\5-10-2019\1999_5mm-7mm\1999_5mm-7mm\20mm_quantiles_3mm-15mm_1999.csv"

year = 1999
Var = 'Abundance'

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

log = False
chronological = False
Fishtype='Delta Smelt'

print 'Now Creating Obs tot Box Whisker Plots'
Var = 'Abundance'
sizes = [3,15]
surveys = [1,2,3,4,5,6,7,8]
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
lfp.make_BoxWhisker(datafile, Var, Log=log, Fishtype=Fishtype)


cohort_data_dir = r'C:\git\longfin_trawl_map\5-10-2019\1999_5mm-7mm\1999_5mm-7mm'
cohort_data = ['dsmelt_quantiles_5mm-7mm_1999-04-01_grow0.30_1999.csv',
               'dsmelt_quantiles_5mm-7mm_1999-04-11_grow0.30_1999.csv',
               'dsmelt_quantiles_5mm-7mm_1999-04-21_grow0.30_1999.csv',
               'dsmelt_quantiles_5mm-7mm_1999-05-01_grow0.30_1999.csv',
               'dsmelt_quantiles_5mm-7mm_1999-05-11_grow0.30_1999.csv',
               'dsmelt_quantiles_5mm-7mm_1999-05-31_grow0.30_1999.csv'
               ]

sizes = [5,7]
surveys = [1,2,3,4,5,6,7,8]
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)

lfp.make_Cohort_BoxWhisker(cohort_data_dir, cohort_data, Var, Log=log, 
                           Fishtype=Fishtype, datatype='cohort', max=900000.)



