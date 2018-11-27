'''
Created on Nov 21, 2018

@author: scott
'''


from Longfin_Plotter import LongfinMaps
import os

Bar = True    #Make bar plots?
BW = False    # Make Box Whisker plots?

years = [2012, 2013, 2016, 2017]
sizes = [[3,11], [12,25]]
surveys = [1,2,3,4,5,6]
BW_paths = [r"J:\Longfin\bar_plots\SLS_quantiles_3mm-11mm_YEAR.csv",
            r"J:\Longfin\bar_plots\SLS_quantiles_12mm-25mm_YEAR.csv"]
longfile_path = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')
fig_dir = '.'

runtype = 'SLS'

for year in years:
    for i, size_range in enumerate(sizes):
        cbm = LongfinMaps(run_dir, grd_file, year)
        #make bar plots
        if Bar:
            figname = os.path.join(fig_dir, 'Bar_Plots')
            print year, size_range, longfile_path
            cbm.runtype = runtype
            cbm.make_Obs_Barplot(longfile_path, figname, size_range, surveys, static_volumes)
        #make boxwhisker
        if BW:
            BW_path = BW_paths[i].replace('YEAR', str(year))
            figname = os.path.join(fig_dir, 'Box_Whisker')
            print year, size_range, BW_path
            cbm.runtype = runtype
            cbm.make_precalc_BoxWhiskerPlot(BW_path, figname, size_range, surveys, static_volumes)
        
print 'done!'