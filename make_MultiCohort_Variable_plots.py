'''
Created on Nov 29, 2018

@author: scott
'''

from Longfin_Plotter import LongfinMaps
import os
import datetime as dt

MC_bar = True
SLS_bar = True
mm20_bar = True
StartTime_MC_bar = True
Chronological_MC_bar = True

years = [2013,2016,2017]
sizes = [[6,10], [12,16]]
surveys = [[3,4,5,6], [1,2,3,4,5,6,7,8,9]]

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

fig_dir = 'Multicohort_Variety_plots'
if not os.path.isdir(fig_dir):
    os.mkdir(fig_dir)


SLS_data = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
mm20_data = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
start_Month = 3
start_Day = 1

for year in years:
    start_Date = dt.datetime(year, start_Month, start_Day)
    for i, size_range in enumerate(sizes):
        if MC_bar:
            print 'making Multicohort bar {0} {1}'.format(size_range, year)
            figname = os.path.join(fig_dir, 'Extended_Cohort_BarPlots')
            cbm = LongfinMaps(run_dir, grd_file, year)
            cbm.multisurveys = surveys
            cbm.runtype = 'sls' #set one the density multiplier
            cbm.make_MultiCohort_Bar_Plot(SLS_data, mm20_data, figname, size_range, static_volumes)
        if SLS_bar:
            print 'making SLS bar {0} {1}'.format(size_range, year)
            figname = figname = os.path.join(fig_dir, 'SLS_Cohort_Plots')
            cbm = LongfinMaps(run_dir, grd_file, year)
            cbm.runtype = 'sls'
            cbm.make_Cohort_Plot(SLS_data, figname, size_range, surveys[0], static_volumes)
        if mm20_bar:
            print 'making 20mm bar {0} {1}'.format(size_range, year)
            figname = figname = os.path.join(fig_dir, 'SLS_Cohort_Plots')
            cbm = LongfinMaps(run_dir, grd_file, year)
            cbm.runtype = '20mm'
            cbm.make_Cohort_Plot(mm20_data, figname, size_range, surveys[1], static_volumes)
        if StartTime_MC_bar:
            print 'making Starttime bar {0} {1}'.format(size_range, year)
            figname = os.path.join(fig_dir, 'Starttime_Cohort_BarPlots')
            cbm = LongfinMaps(run_dir, grd_file, year)
            cbm.multisurveys = surveys
            cbm.runtype = 'sls' #set one the density multiplier
            cbm.make_ST_MultiCohort_Bar_Plot(SLS_data, mm20_data, figname, size_range, static_volumes, start_Date)
        if Chronological_MC_bar:
            print 'making Chronological bar {0} {1}'.format(size_range, year)
            figname = os.path.join(fig_dir, 'Chronological_Cohort_BarPlots')
            cbm = LongfinMaps(run_dir, grd_file, year)
            cbm.multisurveys = surveys
            cbm.runtype = 'sls' #set one the density multiplier
            cbm.make_Chronological_MultiCohort_Bar_Plot(SLS_data, mm20_data, figname, size_range, static_volumes)
print 'done!'