'''
Created on Feb 14, 2019

@author: scott
'''
import os
import datetime  as dt
from Longfin_Plot_Utils import LongfinMap
from Longfin_Plotter_DataManager import DataManager


###########################################################################

class LongfinPlotter(object):
    '''
    Creates and sets up Longfin Plots for trawl data. Calls upon two main scripts:
    Longfin_Plotter_DataManager: Manages and handles data. Reads in data files and organizes
                            them into user defined dataframes. Calculations for 
                            density and abundance are done here. Dataframes can be organized
                            by startdates, chronologically, or growthrates.
    Longfin_Plot_Utils: Handles the actual plotting of the data. Once data is fed in, handles
                        the creation of plot frame, making the plots pretty and saving the plots.
                    
    This class acts a main controller for the longfin plots. This class can be called through other scripts
    (in order to iterate through many files and plots) or called through the main() examples below.
    
    Inputs:
    run_dir: Run directory containing ptm.grd file
    grd_file: Grid file, likely named 'ptm.grd'
    year: Year of the run. currently does not support multiyear data
    sizes: List of the upper and lower bound of the longfin sizes in mm. List is inclusive. ex: [6, 10]
    surveys: takes in a list of surveys to be used for the plot. Each input data file needs its own list of data,
             aka if there are two input data sources, the surveys list should contain 2 lists (ex [[3,4,5,6], [1,2,3,4,5,6,7,8,9]])
             if there is only one data source, a single list suffices (ex [2,3,4,5])
             If there are multiple data sources and the user inputs a single list (see above), all data sources will
             use the selected surveys.
    '''
    def __init__(self,
                 run_dir,
                 grd_file,
                 year,
                 sizes,
                 surveys):
        self.Year = year
        self.Sizes = sizes
        self.Surveys= surveys
        self.Map_Utils = LongfinMap(run_dir, grd_file, self.Year, self.Sizes, self.Surveys) #Create map class object
        
    
    def make_Bars(self,
                  Trawl_Data,
                  static_volumes,
                  Var,
                  Chronological=False, 
                  GrowthRate=0.0,
                  startDate=dt.datetime(1900,1,1),
                  Log=False):
        '''
        Makes Bar Plots and organizes data for plotting. Allows for variable commands to customize plots.
        
        Inputs:
        Trawl_Data: csv file full path containing data. Trawl files must contain a 'SampleDate'
                    field containing the mm/dd/YYYY HH:MM formatted date of the sample. Hour and minute data
                    is typically 00:00 and does not matter.
                    Fields also required: lfs_region, Survey, Year
                    failure to contain these regions will result in a script crash.
        static_volumes: File containing volume of water used for abundance calculations.
                        Must have an entry for each region.
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        GrowthRate: Decimal number value for growth in mm / day. If set to a non zero value, the script will calculate
                     new abundances and densities based the new surveys calculated by the growth rate. Changes survey numbers
                     per region based on how many days from hatch and growth rate.
        startDate: Excludes values that were surveyed before the specified date
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        '''
        
        bar_data = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Bar', static_volumes, startDate=startDate)
        bar_data.InitializeData(Trawl_Data)
        bar_data.apply_Growth(GrowthRate)
        bar_data.apply_Chronological(Chronological)
        data = bar_data.get_DataFrame()
        self.Map_Utils.plot_bars(data, Var, GrowthRate, Chronological, Log, startDate)
        self.Map_Utils.savePlot(Var)
        
    
    
    def make_BoxWhisker(self, 
                        Trawl_Data,
                        Var,
                        Chronological=False,
                        Chronological_data=[],
                        Log=False):
        '''
        Creates boxwhisker plots for properly set up data. Instead of coming from trawl observed data,
        data is post processed into csv files containing the q5, q25, q50, q75, and q95 (q meaning quantile)
        statistics. These values are used for creating boxwhisker plots.
        q5 = 5% quantile, bottom whisker
        q25 = 25% quantile, bottom of the box
        q50 = 50% quantile, middle of the box
        q75 = 75% quantile, top of the box
        q95 = 95% quantile, top whisker
        
        variable controls including chronological and Log scaling. If Chronological, user must include a pairing trawl csv file that contains
        dates for each survey and region.
        
        Inputs:
        Trawl_Data: pre processed csv file full path containing data.
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        Chronological_data: list set of data to correspond with the trawl data. Only needed if Chronological is passed in as True
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        '''
        
        bw_data = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
        bw_data.InitializeData(Trawl_Data)
        bw_data.apply_Chronological(Chronological, Chronological_data=Chronological_data)
        data = bw_data.get_DataFrame()
        self.Map_Utils.plot_boxwhisker(data, Var, Chronological, Log)
        self.Map_Utils.savePlot(Var)
    
    
    def make_PredvsObs_BoxWhisker(self,
                                  Observed_Data_Dir,
                                  Predicted_Data_Dir,
                                  Obs_data_list,
                                  Pred_data_list,
                                  Chronological_data,
                                  Var,
                                  Chronological=False,
                                  Log=False):
        '''
        Creates boxwhisker plots for properly set up data. Instead of coming from trawl observed data,
        data is post processed into csv files containing the q5, q25, q50, q75, and q95 (q meaning quantile)
        statistics. These values are used for creating boxwhisker plots.
        q5 = 5% quantile, bottom whisker
        q25 = 25% quantile, bottom of the box
        q50 = 50% quantile, middle of the box
        q75 = 75% quantile, top of the box
        q95 = 95% quantile, top whisker
        
        The Data acts as a direct comparison of Observed data from collected surveys to computed values.
        
        
        variable controls including chronological and Log scaling. If Chronological, user must include a pairing trawl csv file that contains
        dates for each survey and region.
        
        Inputs:
        Trawl_Data: pre processed csv file full path containing data.
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        Chronological_data: list set of data to correspond with the trawl data. Only needed if Chronological is passed in as True
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        '''

        for i, Pred_data in enumerate(Pred_data_list):
            Cohort_num = int(os.path.basename(Pred_data).split('_')[1].split('.')[0])
            Pred_data_file = os.path.join(Predicted_Data_Dir, Pred_data)
            Obs_data_file = os.path.join(Observed_Data_Dir, Obs_data_list[i])
            print 'Creating Plot for Cohort {0}...'.format(Cohort_num)
            self.Surveys = range(Cohort_num, self.Surveys[-1]+1)
            Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
            Obs_data_Manager.InitializeData(Obs_data_file)
            Obs_data_Manager.get_Dates(Chronological_data)
            Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
            Pred_data_Manager.InitializeData(Pred_data_file, predicted=True)
            Obs_data = Obs_data_Manager.get_DataFrame()
            Avg_Pred_Data = Pred_data_Manager.get_Predicted_Timed_Data(Obs_data)
            dataframe = Pred_data_Manager.merge_Dataframes(Avg_Pred_Data, Obs_data)
            self.Map_Utils.plot_ObsVsPred_Boxwhisker(dataframe, Var, Chronological, Cohort_num, Log)
            self.Map_Utils.savePlot(Var)






############################################################################

if __name__ == '__main__':
    run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
    grd_file = os.path.join(run_dir, 'ptm.grd')
    year = 2013
    bar = True
    box = False
    pvo_boxw = False
    
    
    if bar:
#         Var = 'Density'
        Var = 'Abundance'
        trawl_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"]
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        
        sizes = [6, 10]
        surveys = [[3,4,5,6], [1,2,3,4,5,6,7,8,9]]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
         
        lfp.make_Bars(trawl_data,static_volumes, Var, GrowthRate=.2, Chronological=True, Log=True)
        
    if box:
        Var = 'Abundance'
        trawl_data = [r"J:\Longfin\bar_plots\SLS_quantiles_12mm-16mm_2012-3-1_grow0.30_2012.csv", r"J:\Longfin\from_Ed\20mm_quantiles_12mm-16mm_2012-3-1_grow0.20_2012.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"]
        sizes = [12,16]
        surveys = [[1,2,3,4,5,6], [1,2,3,4,5,6,7,8,9]]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
         
        lfp.make_BoxWhisker(trawl_data, Var, Chronological=True, Chronological_data=Chron_data, Log=True)
        
    if pvo_boxw:
        Var = 'Abundance'
        Pred_data_dir = r"C:\git\longfin_trawl_map\hatching_fit_multiple_cohorts"
        Obs_data_dir = r"C:\git\longfin_trawl_map\SLS"
        Pred_data = ["quantiles_1.csv",
                     "quantiles_2.csv",
                     "quantiles_3.csv",
                     "quantiles_4.csv",
                     "quantiles_5.csv",
                     "quantiles_6.csv"]
        Obs_data = ['SLS_quantiles_4mm-8mm_2012-12-21_grow0.20_2013.csv', 
                    'SLS_quantiles_4mm-8mm_2013-01-03_grow0.20_2013.csv',
                    "SLS_quantiles_4mm-8mm_2013-01-15_grow0.20_2013.csv",
                    "SLS_quantiles_4mm-8mm_2013-01-29_grow0.20_2013.csv",
                    "SLS_quantiles_4mm-8mm_2013-02-12_grow0.20_2013.csv",
                    "SLS_quantiles_4mm-8mm_2013-02-26_grow0.20_2013.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [4,8]
        surveys = [1,2,3,4,5,6]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
         
        lfp.make_PredvsObs_BoxWhisker(Obs_data_dir, Pred_data_dir, Obs_data, Pred_data, Chron_data, Var, Log=True)
    
    
    
    