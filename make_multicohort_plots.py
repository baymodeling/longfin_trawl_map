'''
Created on Nov 29, 2018

@author: scott
'''

from Longfin_Plotter import LongfinMaps
import os

bar = False
BW = True

years = [2012,2013,2016,2017]
sizes = [[3,11], [12,25]]
surveys = [[3,4,5,6], [2,3,4,5,6,7,8,9]]

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')

fig_dir = 'Multicohort_plots'
if not os.path.isdir(fig_dir):
    os.mkdir(fig_dir)
BW_paths = [[r"J:\Longfin\bar_plots\SLS_quantiles_3mm-11mm_YEAR.csv", r"J:\Longfin\bar_plots\20mm_quantiles_small_larvae_YEAR.csv"],
            [r"J:\Longfin\bar_plots\SLS_quantiles_12mm-25mm_YEAR.csv", r"J:\Longfin\bar_plots\20mm_quantiles_larvae_YEAR.csv"]]

obs_data1 = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
obs_data2 = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"


for year in years:
    for i, size_range in enumerate(sizes):
        if bar:
            figname = os.path.join(fig_dir, 'Extended_Cohort_BarPlots')
            cbm = LongfinMaps(run_dir, grd_file, year)
            cbm.multisurveys = surveys
            cbm.runtype = 'sls' #set one the density multiplier
            cbm.make_MultiCohort_Bar_Plot(obs_data1, obs_data2, figname, size_range, static_volumes)
        if BW:
            figname = os.path.join(fig_dir, 'Extended_Cohort_BoxPlots')
            BW_path1 = BW_paths[i][0].replace('YEAR', str(year))
            BW_path2 = BW_paths[i][1].replace('YEAR', str(year))
            cbm = LongfinMaps(run_dir, grd_file, year)
            cbm.multisurveys = surveys
            cbm.runtype = 'sls' #set one the density multiplier
            cbm.make_MultiCohort_BoxWhisker_Plot(BW_path1, BW_path2, figname, size_range, static_volumes)
        
print 'done!'