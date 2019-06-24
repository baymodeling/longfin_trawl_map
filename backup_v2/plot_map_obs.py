import os
import pdb
import map_w_bars
import CAMT_bar_maps
import ptm_inp_reader
import fit_results
import ptm_time_utils

run_dir = 'F:\PTM_simulations\CAMT\Dec20_2001_sac_bt\Run'
fig_dir = r'.\figs'
# add option to get all group names for directory
year = 2002
grd_file = os.path.join(run_dir,'FISH_PTM.grd')
cbm = CAMT_bar_maps.CamtBarMaps(run_dir, grd_file)
cbm.get_inputs()

figname = os.path.join(fig_dir, 'obs_frac_2002.png')
#cbm.plot_map_obs(year, figname)

# plot observed regional abundanc
base_fitdir = r'..\fitting_max_pop_skt_sal'
#obs_file = os.path.join(base_fitdir,r'inputs\DS_Data_Dec-20-01_4m.txt')
obs_file = os.path.join(base_fitdir,r'inputs\DS_Data_Dec-05-01_4m.txt')
figname = os.path.join(fig_dir, 'obs_abundance_2002.png')
movdir = r'..\movement_table'
gname = 'passive'
release_time_string = '2001-12-05 00:00'
rtime = ptm_time_utils.get_datenum_from_string(release_time_string)
cbm.plot_map_obs_fish(obs_file, year, movdir, gname, rtime, figname)
