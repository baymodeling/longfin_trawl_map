'''
Created on Apr 12, 2019

@author: scott
'''

import os
import datetime as dt
from Longfin_Plotter import LongfinPlotter


###Data Inputs###

Pred_data_dir = r"C:\git\longfin_trawl_map\4-16-2019\hatching_fit_15day_cohorts"
predicted_data = ["quantiles.csv"]
hatch_file = "hatch_quantiles.csv"
entrainment_file = "entrainment_quantiles.csv"
prop_entrainment_file = 'proportional_entrainment.csv'
total_pred_data = "tot_quantiles.csv"
total_obs_data = "SLS_quantiles_3mm-18mm_2013.csv"
Obs_data_dir = r"C:\git\longfin_trawl_map\4-16-2019\2013_4mm-7mm\2013_4mm-7mm\SLS"
Obs_Cohort_Data = ["SLS_quantiles_4mm-7mm_2012-12-13_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2012-12-28_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-01-12_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-01-27_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-02-11_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-02-26_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-03-13_grow0.20_2013.csv"]

chronological_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"


sizes = [4,7]
surveys = [1,2,3,4,5,6] #surveys are cohorts for Hatch and Entrainment plots
year = 2013
Var = 'Abundance'

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

log = False
chronological = True

print 'Now Creating Hatching Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
hatch_file = os.path.join(Pred_data_dir, hatch_file)
lfp.make_BoxWhisker(hatch_file, Var, Log=log, datatype='hatch',max=5000000000.)
  
print 'Now Creating Entrainment Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
entrainment_file = os.path.join(Pred_data_dir, entrainment_file)
lfp.make_BoxWhisker(entrainment_file, Var, Log=log, datatype='entrainment',max=9000000.)


print 'Now Creating Pred vs Obs'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)     
lfp.make_PredvsObs_BoxWhisker(Obs_data_dir, Pred_data_dir, Obs_Cohort_Data, predicted_data, chronological_data, 
                              Var, Log=log, datatype='condensed_predicted',max=5000000000.)

print 'Now Creating Timeseries Plots'
Var = 'Larvae'
entrainment_file = os.path.join(Pred_data_dir, prop_entrainment_file)
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_TimeSeries_Plots(entrainment_file, Var, datatype='fractional_entrainment', max=.4)

print 'Now Creating Total Pred vs Obs'
Var = 'Abundance'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_TotalPredvsObs_BoxWhisker(Pred_data_dir, Obs_data_dir, total_pred_data, total_obs_data, 
                                   chronological_data, Var, Log=log)
