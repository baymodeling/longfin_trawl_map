'''
Created on Jun 19, 2019

@author: scott
@organization: Resource Management Associates
@contact: scott@rmanet.com
@note:
'''

from Longfin_Plotter import LongfinPlotter
import os

run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
grd_file = os.path.join(run_dir, 'ptm.grd')
year = 2013
Var = 'Larvae'
Pred_data = r"C:\git\longfin_trawl_map\new_predicted_06132019\results\results\predicted_cohort_source_entrainment_quantiles.csv"
sizes = [6,9]
cohorts = [1,2,3,4,5,6]
max = 20000000.
lfp = LongfinPlotter(run_dir, grd_file, year, sizes, cohorts=cohorts)
lfp.make_BoxWhisker(Pred_data, Var, datatype='entrainment', Log=False, max=max)