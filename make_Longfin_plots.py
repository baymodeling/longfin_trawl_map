'''
Created on Nov 21, 2018

@author: scott
'''


from Longfin_bar_maps import LongfinBarMaps
import os

years = [2012, 2013, 2016, 2017]
sizes = [[3,11], [12,25]]
surveys = [1,2,3,4,5,6,7,8,9]

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')
fig_dir = '.'

for year in years:
    for size_range in sizes:
        cbm = LongfinBarMaps(run_dir, grd_file, year)
        bm_inputs = cbm.get_inputs()
        #make bar plots
        figname = os.path.join(fig_dir, 'obs_Bar_Plots')
        cbm.plot_map_obs(figname, size_range, surveys)
        #make boxwhisker
        figname = os.path.join(fig_dir, 'obs_Box_Whisker')
        cbm.plot_obs_boxwhisker(figname, size_range, surveys)
        
print 'done!'