'''
Created on Jul 2, 2019

@author: scott
@organization: Resource Management Associates
@contact: scott@rmanet.com
@note:
'''
from Longfin_Plotter import LongfinPlotter
import os
import matplotlib
matplotlib.use('Agg')
matplotlib.use('Qt4Agg')

#data_dir = r"R:\RMA\Projects\Longfin\Analysis\R\combined_analysis_delta_smelt_raw\dsmelt_1999_5mm_15mm_max_0.20grow\results"
data_dir = r"R:\RMA\Projects\Longfin\Analysis\R\combined_analysis_delta_smelt_raw\alpha8\dsmelt_1999_5mm_15mm_max_0.20grow\results"

run_dir = r'R:\PTM\Longfin\1999_delta_smelt_cohort_run_2\Run'
grd_file = os.path.join(run_dir, 'FISH_PTM.grd')
year = 1999
fishtype = 'Delta Smelt'
#output_directory = r'R:\RMA\Projects\Longfin\Analysis\R\combined_analysis_delta_smelt_raw\dsmelt_1999_5mm_15mm_max_0.20grow\plots'
output_directory = r'R:\RMA\Projects\Longfin\Analysis\R\combined_analysis_delta_smelt_raw\alpha8\dsmelt_1999_5mm_15mm_max_0.20grow\plots'
surveys = [1,2,3,4,5,6,7]
cohorts = [1,2,3,4,5,6,7,8,9]
abu_max = 5.e06
hatching_period=10 # days

#total Plots
Var = 'Abundance'
Title = 'hatch 5mm, growth 0.2 mm/day'
Obs_Label = 'Observed'
Pred_Label = 'Predicted'
Obs_total_data = os.path.join(data_dir, "observed_total_abundance_quantiles.csv")
Pred_total_data = os.path.join(data_dir, "predicted_total_abundance_quantiles.csv")
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, 
#                    hatching_period=hatching_period,
                     title=Title, output_directory=output_directory)
lfp.make_TotalPredvsObs_BoxWhisker(Obs_total_data, Pred_total_data, Var, Log=False, Obs_Label=Obs_Label, Pred_Label=Pred_Label, Fishtype=fishtype, max=abu_max, cohort_data=False)


#plot pred vs obs
Var = 'Abundance'
Obs_data = os.path.join(data_dir, "observed_cohort_abundance_quantiles.csv")
Pred_data = os.path.join(data_dir, "predicted_cohort_abundance_quantiles.csv")
lfp = LongfinPlotter(run_dir, grd_file, year, surveys=surveys, 
                     cohorts=cohorts, hatching_period=hatching_period,
                     title=Title, output_directory=output_directory)
lfp.make_PredvsObs_BoxWhisker(Obs_data, Pred_data, Var, Log=False, Obs_Label=Obs_Label, Pred_Label=Pred_Label, Fishtype=fishtype, max=abu_max)


#Plot Entrainment
Var = 'Larvae'
Pred_Entrainment_data = os.path.join(data_dir, "predicted_cohort_source_entrainment_quantiles.csv")
#max = 20000000.
lfp = LongfinPlotter(run_dir, grd_file, year, cohorts=cohorts, title=Title, output_directory=output_directory)
lfp.make_BoxWhisker(Pred_Entrainment_data, Var, datatype='entrainment', Log=False, max=abu_max, Fishtype=fishtype)

#plot regional hatch
Pred_hatch_data = os.path.join(data_dir, "cohort_hatch_quantiles.csv")
#max=5000000000.
Var = 'Larvae'
lfp = LongfinPlotter(run_dir, grd_file, year, cohorts=cohorts, title=Title, output_directory=output_directory)
lfp.make_BoxWhisker(Pred_hatch_data, Var, datatype='hatch', Log=False, Fishtype=fishtype, max=abu_max)




