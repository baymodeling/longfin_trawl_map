'''
Created on Nov 21, 2018

@author: scott
'''


from Longfin_bar_maps import LongfinBarMaps
import os

years = [2012, 2013, 2016, 2017]
sizes = [[3,11], [12,25]]
surveys = [1,2,3,4,5,6,7,8,9]
BW_paths = [r"J:\Longfin\bar_plots\20mm_quantiles_small_larvae_YEAR.csv",
            r"J:\Longfin\bar_plots\20mm_quantiles_larvae_YEAR.csv"]
longfile_path = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')
fig_dir = '.'

for year in years:
    for i, size_range in enumerate(sizes):
        cbm = LongfinBarMaps(run_dir, grd_file, year)
        bm_inputs = cbm.get_inputs()
        #make bar plots
        figname = os.path.join(fig_dir, 'obs_Bar_Plots')
        print year, size_range, longfile_path
        cbm.plot_map_obs(longfile_path, figname, size_range, surveys)
        #make boxwhisker
        BW_path = BW_paths[i].replace('YEAR', str(year))
        figname = os.path.join(fig_dir, 'obs_Box_Whisker')
        print year, size_range, BW_path
        cbm.plot_obs_boxwhisker(BW_path, figname, size_range, surveys)
        
print 'done!'