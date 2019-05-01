'''
Created on Feb 14, 2019

@author: scott
'''
import os, sys
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
                  Log=False,
                  max=0.):
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
        self.Map_Utils.plot_bars(data, Var, GrowthRate, Chronological, Log, startDate, max=max)
        self.Map_Utils.savePlot(Var)
        
    
    
    def make_BoxWhisker(self, 
                        Trawl_Data,
                        Var,
                        Chronological=False,
                        Chronological_data=[],
                        Log=False,
                        datatype=None,
                        max=0.):
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
        bw_data.InitializeData(Trawl_Data, datatype=datatype)
        bw_data.apply_Chronological(Chronological, Chronological_data=Chronological_data)
        data = bw_data.get_DataFrame()
        self.Map_Utils.plot_boxwhisker(data, Var, Chronological, Log, datatype=datatype, max=max)
        self.Map_Utils.savePlot(Var)
    
    
    def make_PredvsObs_BoxWhisker(self,
                                  Observed_Data_Dir,
                                  Predicted_Data_Dir,
                                  Obs_data_list,
                                  Pred_data_list,
                                  Chronological_data,
                                  Var,
                                  Chronological=False,
                                  Log=False,
                                  max=0.,
                                  datatype=None):
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
        Cohorts = self.Surveys #because these are set in a different function, they function about the same
                                #are renamed here for clarity sake. 
        
        if datatype == 'condensed_predicted':
            if len(Pred_data_list) > 1:
                print 'too many data files for condensed. Now exiting...'
                sys.exit(0) 
            Pred_data_file = os.path.join(Predicted_Data_Dir, Pred_data_list[0])
            Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
            Pred_data_Manager.InitializeData(Pred_data_file, datatype='condensed_predicted')
            
            for i, Cohort in enumerate(Cohorts):
                Obs_data_file = os.path.join(Observed_Data_Dir, Obs_data_list[i])
                Cohorts = range(Cohort, Cohorts[-1]+1)
                Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
                Obs_data_Manager.InitializeData(Obs_data_file)
                Obs_data_Manager.get_Dates(Chronological_data)
                Obs_data = Obs_data_Manager.get_DataFrame()
                Avg_Pred_Data = Pred_data_Manager.get_Predicted_Timed_Data(Obs_data, datatype='condense_predicted', cohort=i+1)
                dataframe = Pred_data_Manager.merge_Dataframes(Avg_Pred_Data, Obs_data)
                self.Map_Utils.plot_ObsVsPred_Boxwhisker(dataframe, Var, Chronological, Cohort, Log, max=max)
                self.Map_Utils.savePlot(Var)
        
        else:
            for i, Pred_data in enumerate(Pred_data_list):
                Cohort_num = int(os.path.basename(Pred_data).split('_')[1].split('.')[0])
                Pred_data_file = os.path.join(Predicted_Data_Dir, Pred_data)
                Obs_data_file = os.path.join(Observed_Data_Dir, Obs_data_list[i])
                print 'Creating Plot for Cohort {0}...'.format(Cohort_num)
                self.Surveys = range(Cohort_num, self.Surveys[-1]+1)
                Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
                Obs_data_Manager.InitializeData(Obs_data_file)
#                 obsstartdate= Obs_data_list[i].split('_')[3]
#                 obsenddate = Obs_data_list[i].split('_')[3]
                Obs_data_Manager.get_Dates(Chronological_data)
                Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
                Pred_data_Manager.InitializeData(Pred_data_file, datatype='predicted')
                Obs_data = Obs_data_Manager.get_DataFrame()
                Avg_Pred_Data = Pred_data_Manager.get_Predicted_Timed_Data(Obs_data)
                dataframe = Pred_data_Manager.merge_Dataframes(Avg_Pred_Data, Obs_data)
                self.Map_Utils.plot_ObsVsPred_Boxwhisker(dataframe, Var, Chronological, Cohort_num, Log, max=max)
                self.Map_Utils.savePlot(Var)
            
    def make_MultiPredvsObs_BoxWhisker(self,
                                  Observed_Data_Dir,
                                  Predicted_Data_Dir,
                                  Obs_data_list,
                                  Pred_data_list,
                                  Chronological_data,
                                  Var,
                                  Chronological=False,
                                  Log=False,
                                  max=0.):
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
        cur_Dir = os.getcwd()
        Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
        os.chdir(Predicted_Data_Dir)
        Pred_data_Manager.InitializeData(Pred_data_list, datatype='multipredicted')
        Pred_data_Manager.apply_Chronological(Chronological, Chronological_data=Chronological_data)
        os.chdir(Observed_Data_Dir)
        Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
        Obs_data_Manager.InitializeData(Obs_data_list)
        Obs_data_Manager.get_Dates(Chronological_data)
        Obs_data = Obs_data_Manager.get_DataFrame()
        
        Avg_Pred_Data = Pred_data_Manager.get_Predicted_Timed_Data(Obs_data, datatype='multipredicted')
        dataframe = Pred_data_Manager.merge_Dataframes(Avg_Pred_Data, Obs_data)
        self.Map_Utils.plot_ObsVsPred_Boxwhisker(dataframe, Var, Chronological, 'Total', Log, datatype='multipredicted', max=max)
        self.Map_Utils.savePlot(Var)
        


    def make_TotalPredvsObs_BoxWhisker(self,
                              Predicted_Data_Dir,
                              Obs_Data_Dir,
                              Pred_data_list,
                              Obs_data_list,
                              Chronological_data,
                              Var,
                              Chronological=False,
                              Log=False,
                              max=0.):
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
        Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
#         Obs_data_Manager.InitializeData(Obs_data)
        for i, Obs_data in enumerate(Obs_data_list):
            Obs_data_file = os.path.join(Obs_Data_Dir, Obs_data)
            Obs_data_Manager.InitializeData(Obs_data_file)
        Obs_data_Manager.get_Dates(Chronological_data)
        Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
        for i, Pred_data in enumerate(Pred_data_list):
            Pred_data_file = os.path.join(Predicted_Data_Dir, Pred_data)
            Pred_data_Manager.InitializeData(Pred_data_file, datatype='predicted')
            
        Obs_data = Obs_data_Manager.get_DataFrame()
        Avg_Pred_Data = Pred_data_Manager.get_Predicted_Timed_Data(Obs_data, datatype='total')
        dataframe = Pred_data_Manager.merge_Dataframes(Avg_Pred_Data, Obs_data)
        self.Map_Utils.plot_ObsVsPred_Boxwhisker(dataframe, Var, Chronological, 'Total', Log, max=max)
        self.Map_Utils.savePlot(Var)
        
    def make_Cohort_BoxWhisker(self,
                              Data_dir,
                              data_files,
                              Var,
                              Log=False,
                              datatype=None,
                              max=0.):
        cohorts = self.Surveys
        for cohort in cohorts:
            print 'Creating Plot for Cohort {0}...'.format(cohort)
            self.Surveys = range(cohort, self.Surveys[-1]+1)
            bw_data = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'Boxwhisker', '')
            for datafile in data_files:
                Trawl_Data = os.path.join(Data_dir, datafile)
                bw_data.InitializeData(Trawl_Data)
            data = bw_data.get_DataFrame()
            self.Map_Utils.plot_boxwhisker(data, Var, '', Log, datatype=datatype, cohortNum=cohort, max=max)
            self.Map_Utils.savePlot(Var)


    def make_TimeSeries_Plots(self,
                              Datafile,
                              Log=False,
                              datatype=None,
                              max=0.):

        data = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, self.Surveys, 'timeseries', '')
        data.InitializeData(Datafile)
        data = data.get_DataFrame()
        self.Map_Utils.plot_timeseries(data, Var, Log, datatype=datatype, max=max)
        self.Map_Utils.savePlot(Var)

############################################################################

if __name__ == '__main__':
    run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
    grd_file = os.path.join(run_dir, 'ptm.grd')
    year = 2013
    bar = False
    box = False
    pvo_boxw = False
    pvo_boxw_Total = False
    hatch = True
    entrainment = False
    PredvsMultiObs = False
    CohortBW = False
    EntrainmentTS = False
    
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
        Pred_data_dir = r"C:\git\longfin_trawl_map\4-16-2019\alpha3"
        Obs_data_dir = r"C:\git\longfin_trawl_map\4-16-2019\SLS\SLS"
        Pred_data = ["quantiles_1.csv",
                     "quantiles_2.csv",
                     "quantiles_3.csv",
                     "quantiles_4.csv",
                     "quantiles_5.csv",
                     "quantiles_6.csv"]
        Obs_data  = ["SLS_quantiles_4mm-7mm_2012-12-13_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2012-12-28_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-01-12_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-01-27_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-02-11_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-02-26_grow0.20_2013.csv",
                     "SLS_quantiles_4mm-7mm_2013-03-13_grow0.20_2013.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [4,7]
        surveys = [1,2,3,4,5,6,7]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
         
        lfp.make_PredvsObs_BoxWhisker(Obs_data_dir, Pred_data_dir, Obs_data, Pred_data, Chron_data, Var, Log=False)

    if pvo_boxw_Total:
        Var = 'Abundance'
        Pred_data_dir = r"C:\git\longfin_trawl_map\4-11-2019"
        Obs_data_dir = r"C:\git\longfin_trawl_map\4-11-2019"
        Pred_data = ["tot_quantiles.csv"]
        Obs_data = ["SLS_quantiles_3mm-11mm_2013.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [3,11]
        surveys = [1,2,3,4,5,6]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
         
        lfp.make_TotalPredvsObs_BoxWhisker(Pred_data_dir, Obs_data_dir, Pred_data, Obs_data, Chron_data, Var, Log=False)
    
    
    if hatch:
        Var = 'Larvae'
        trawl_data = [r"C:\git\longfin_trawl_map\4-16-2019\grow_27\hatch_quantiles.csv"]
        sizes = []
        cohorts = [1,2,3,4,5,6,7]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, cohorts)
         
        lfp.make_BoxWhisker(trawl_data, Var, Log=False, datatype='hatch', max=5000000000.)
        
    if entrainment:
        Var = 'Larvae'
        trawl_data = [r"C:\git\longfin_trawl_map\4-16-2019\grow_27\entrainment_quantiles.csv"]
        sizes = []
        cohorts = [1,2,3,4,5,6,7]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, cohorts)
         
        lfp.make_BoxWhisker(trawl_data, Var, Log=False, datatype='entrainment',max=20000000.)
        
    if PredvsMultiObs:
        Var = 'Abundance'
        predicted_data_dir = r'C:\git\longfin_trawl_map\multipredicted_test'
        observed_data_dir = r'C:\git\longfin_trawl_map\multipredicted_test'
        Observed_data = "SLS_quantiles_3mm-11mm_2013.csv"
        predicted_data = ["tot_quantiles.csv",
                          "tot_quantiles_2.csv",
                          "tot_quantiles_3.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [3,11]
        surveys = [1,2,3]
        
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
        lfp.make_MultiPredvsObs_BoxWhisker(observed_data_dir, predicted_data_dir, Observed_data, predicted_data, Chron_data, Var, Log=True)
         
    if CohortBW:
        Obs_data_dir = r"C:\git\longfin_trawl_map\4-16-2019"
        observed_data = ["20mm_quantiles_3mm-18mm_2013.csv"]
        Var = 'Abundance'
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [4,7]
        cohorts = [1,2,3,4,5,6,7]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, cohorts)
         
        lfp.make_Cohort_BoxWhisker(Obs_data_dir, observed_data, Var, Log=True, datatype='cohort')
        
    if EntrainmentTS:
        Var = 'Larvae'
        sizes=[]
        surveys = [1,2,3,4,5,6]
        entrainment_files = r"C:\git\longfin_trawl_map\4-16-2019\alpha3\proportional_entrainment.csv"
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys)
        lfp.make_TimeSeries_Plots(entrainment_files, datatype='fractional_entrainment', max=1.)
                             
