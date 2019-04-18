'''
Created on Apr 12, 2019

@author: scott
'''

import os
import datetime as dt
from Longfin_Plotter import LongfinPlotter

hatch_file = [r"C:\git\longfin_trawl_map\4-16-2019\hatching_fit_15day_cohorts\hatch_quantiles.csv"]
entrainment_file = [r"C:\git\longfin_trawl_map\4-16-2019\hatching_fit_15day_cohorts\entrainment_quantiles.csv"]
Pred_data_dir = r"C:\git\longfin_trawl_map\4-16-2019\2013_4mm-7mm\2013_4mm-7mm\SLS"
predicted_total_data = ["SLS_totals_4mm-7mm_2012-12-13_grow0.20_2013.csv",
                        "SLS_totals_4mm-7mm_2012-12-28_grow0.20_2013.csv",
                        "SLS_totals_4mm-7mm_2013-01-12_grow0.20_2013.csv",
                        "SLS_totals_4mm-7mm_2013-02-11_grow0.20_2013.csv",
                        "SLS_totals_4mm-7mm_2013-02-26_grow0.20_2013.csv",
                        "SLS_totals_4mm-7mm_2013-03-13_grow0.20_2013.csv"]
Obs_data_dir = r"C:\git\longfin_trawl_map\4-16-2019"
observed_data = ["SLS_quantiles_3mm-18mm_2013.csv"]
chronological_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
Pred_Cohort_Data = ["SLS_quantiles_4mm-7mm_2012-12-13_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2012-12-28_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-01-12_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-01-27_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-02-11_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-02-26_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-03-13_grow0.20_2013.csv"]
Obs_Cohort_Data = ['SLS_quantiles_4mm-8mm_2012-12-21_grow0.20_2013.csv', 
                    'SLS_quantiles_4mm-8mm_2013-01-03_grow0.20_2013.csv',
                    "SLS_quantiles_4mm-8mm_2013-01-15_grow0.20_2013.csv",
                    "SLS_quantiles_4mm-8mm_2013-01-29_grow0.20_2013.csv",
                    "SLS_quantiles_4mm-8mm_2013-02-12_grow0.20_2013.csv",
                    "SLS_quantiles_4mm-8mm_2013-02-26_grow0.20_2013.csv"]

static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"


sizes = [4,7]
surveys = [1,2,3,4,5,6] #surveys are cohorts for Hatch and Entrainment plots
cohorts = [1,2,3,4,5,6,7]
year = 2013
Var = 'Abundance'

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

log = False
chronological = True

'''
print 'Now Creating Hatching Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(hatch_file, Var, Log=log, datatype='hatch',max=5000000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\hatching_fit_15day_cohorts')
  
print 'Now Creating Entrainment Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(entrainment_file, Var, Log=log, datatype='entrainment',max=9000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\hatching_fit_15day_cohorts')

 
hatch_file = r"C:\git\longfin_trawl_map\4-16-2019\alpha3\hatch_quantiles.csv"
entrainment_file = r"C:\git\longfin_trawl_map\4-16-2019\alpha3\entrainment_quantiles.csv"
 
print 'Now Creating Hatching Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(hatch_file, Var, Log=log, datatype='hatch', max=5000000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\alpha3')

print 'Now Creating Entrainment Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(entrainment_file, Var, Log=log, datatype='entrainment', max=9000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\alpha3') 
 
print 'Now Creating Cohort Boxwhisker Plot...'
Var = 'Abundance'
lfp = LongfinPlotter(run_dir, grd_file, year, [3,18], surveys)
lfp.make_BoxWhisker(os.path.join(Obs_data_dir, observed_data[0]), Var, Chronological=False, 
                    Chronological_data=chronological_data, Log=False, max=5000000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output') 

# print 'Now Creating Total Pred vs Obs'
# lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)     
# lfp.make_TotalPredvsObs_BoxWhisker(r"C:\git\longfin_trawl_map\4-16-2019", Obs_data_dir, ["tot_quantiles.csv"], 
#                                    observed_data, chronological_data, Var, Log=False, max=5000000000.)
# lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output') 

'''

'''
for i, cohort_file in enumerate(Pred_Cohort_Data):
    print 'Now Creating Cohort Boxwhisker Plot {0}...'.format(i + 1)
    Var = 'Abundance'
    lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
    lfp.make_BoxWhisker(os.path.join(Pred_data_dir, cohort_file), Var, Chronological=False, 
                        Chronological_data=chronological_data, Log=False, max=5000000000.)
    lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\Cohort', addName=i+1) 
'''
'''
print 'Now Creating Total Pred vs Obs'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)     
lfp.make_TotalPredvsObs_BoxWhisker(r"C:\git\longfin_trawl_map\4-16-2019\alpha3", Obs_data_dir, ["quantiles.csv"], 
                                   observed_data, chronological_data, Var, Log=False, max=5000000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\alpha3', addName='alpha3') 
'''

print 'Now Creating Total Pred vs Obs'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)     
lfp.make_PredvsObs_BoxWhisker(r'C:\git\longfin_trawl_map\4-16-2019\SLS\SLS', r"C:\git\longfin_trawl_map\4-16-2019\hatching_fit_15day_cohorts",
                                   Pred_Cohort_Data, ["quantiles.csv"], chronological_data, Var, Log=False, max=5000000000., datatype='condensed_predicted')
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\hatching_fit_15day_cohorts', addName='fit15day') 

'''
print 'Now Creating Cohort Boxwhisker Plot...'
Var = 'Abundance'
lfp = LongfinPlotter(run_dir, grd_file, year, [3,18], surveys)
lfp.make_TotalPredvsObs_BoxWhisker(r'C:\git\longfin_trawl_map\4-16-2019', Obs_data_dir, ['tot_quantiles.csv'], observed_data, chronological_data, Var, Log=False, max=5000000000.)

lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output') 
'''

'''
print 'Now Creating Entrainment Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(entrainment_file, Var, Log=log, datatype='entrainment',max=20000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\hatching_fit_15day_cohorts')

entrainment_file = r"C:\git\longfin_trawl_map\4-16-2019\alpha3\entrainment_quantiles.csv"
 
print 'Now Creating Entrainment Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(entrainment_file, Var, Log=log, datatype='entrainment', max=20000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\alpha3') 
'''
'''
#Growth27
print 'Now Creating Hatching Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(hatch_file, Var, Log=log, datatype='hatch',max=5000000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\hatching_fit_15day_cohorts')
  
print 'Now Creating Entrainment Plot...'
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
lfp.make_BoxWhisker(entrainment_file, Var, Log=log, datatype='entrainment',max=9000000.)
lfp.Map_Utils.movePlot(r'C:\git\longfin_trawl_map\4-16-2019\output\hatching_fit_15day_cohorts')
'''