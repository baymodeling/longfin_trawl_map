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
    surveys/cohorts: takes in a list of surveys to be used for the plot. Each input data file needs its own list of data,
             aka if there are two input data sources, the surveys list should contain 2 lists (ex [[3,4,5,6], [1,2,3,4,5,6,7,8,9]])
             if there is only one data source, a single list suffices (ex [2,3,4,5])
             If there are multiple data sources and the user inputs a single list (see above), all data sources will
             use the selected surveys.
             User MUST specify whether they are passing in surveys or passing in cohorts. Most of the time, user will be passing in
             surveys. The easiest way to tell is to look at the data sources. Depending on the user selection, the headers for
             the data will be read differently. If an input file says 'survey', pass in surveys.
             Survey/cohorts are converted to 'Groups'. The datatype (survey/cohort) is mantained for reference.
    '''
    def __init__(self,
                 run_dir,
                 grd_file,
                 year,
                 sizes=None,
                 surveys=None,
                 cohorts=None,
                 title='',
                 output_directory=''):
        
        self.Year = year
        self.Sizes = sizes
        self.Surveys = surveys 
        self.Cohorts = cohorts
        self.output_directory = output_directory
        self.Map_Utils = LongfinMap(run_dir, grd_file, self.Year, self.Sizes, self.Cohorts, self.Surveys, title=title) #Create map class object
#         self.Map_Utils.Total_Groups = self.Groups

    def get_inputs(self, flag):
        inputs = {}
        input_File = 'inputs.txt'
        with open(input_File) as InF:
            for line in InF:
                if '#' != line[0]:
                    sline = line.split('=')
                    if flag in sline[0]:
                        if sline[0] not in inputs.keys():
                            inputs[sline[0].strip()] = sline[1].strip()
                        elif inputs[sline[0].strip()] != list:
                            inputs[sline[0].strip()] = [inputs[sline[0].strip()]]
                            inputs[sline[0].strip()].append(sline[1].strip())
                        else:
                            inputs[sline[0].strip()].append(sline[1].strip())
                        
        return inputs
            
        
    def make_Bars(self,
                  Trawl_Data,
                  static_volumes,
                  Var,
                  Chronological=False, 
                  GrowthRate=0.0,
                  startDate=dt.datetime(1900,1,1),
                  Log=False,
                  max=0.,
                  Fishtype='Longfin Smelt'):
        '''
        Makes Bar Plots and organizes data for plotting. Allows for variable commands to customize plots.
        
        Inputs:
        Trawl_Data: csv file full pathe mm/dd/YYYY HH:MM formatted date of the sample. Hour and minute data
                    is typically 00:00 and does not matter.
                    Fields also required:h containing data. Trawl files must contain a 'SampleDate'
                    field containing t lfs_region, Survey, Year
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
        
        bar_data = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Bar', static_volumes, 
                               self.Groups, self.Group_Type, startDate=startDate)
        bar_data.InitializeData(Trawl_Data)
        bar_data.apply_Growth(GrowthRate)
        bar_data.apply_Chronological(Chronological)
        data = bar_data.get_DataFrame()
        self.Map_Utils.plot_bars(data, Var, GrowthRate, Chronological, Log, Fishtype, startDate, max=max)
        self.Map_Utils.savePlot(Var)
        
    
    
    def make_BoxWhisker(self, 
                        Trawl_Data,
                        Var,
                        Chronological=False,
                        Log=False,
                        datatype=None,
                        max=0.,
                        Fishtype='Longfin Smelt'):
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
        Max: set a max value used for plotting. Otherwise use the highest q50 value.
        '''
        if self.Map_Utils.title_str == '':
            if datatype == 'entrainment':
                inputs = self.get_inputs('ENT')
                self.Map_Utils.title_str = inputs['ENT_Title']
            elif datatype == 'hatch':
                inputs = self.get_inputs('HATCH')
                self.Map_Utils.title_str = inputs['HATCH_Title']
        bw_data =  DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                               self.Cohorts, self.Surveys)
        bw_data.InitializeData(Trawl_Data, datatype=datatype, Label='Computed')
#         if self.Groups != None:
#             bw_data.apply_Chronological(Chronological, Chronological_data=Chronological_data)
        dataframe = bw_data.get_DataFrame()
        dataframe = bw_data.Organize_Data(dataframe, datatype)
        self.Map_Utils.plot_boxwhisker(dataframe, Var, Chronological, Log, Fishtype, datatype=datatype, max=max)
        self.Map_Utils.savePlot(Var)
    
    
    def make_PredvsObs_BoxWhisker(self,
                                  Obs_data_file,
                                  Pred_data_file,
                                  Var,
                                  Chronological=False,
                                  Log=False,
                                  max=0.,
                                  Fishtype='Longfin Smelt',
                                  Obs_Label=None,
                                  Pred_Label=None
                                  ):
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
        Observed_Data_Dir: path to directory where observed data exists.
        Predicted_Data_Dir: path to directory where predicted data exists.
        Obs_data_list: list of observed data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Pred_data_list: list of Predicted data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        Chronological_data: list set of data to correspond with the trawl data. Only needed if Chronological is passed in as True
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        Max: set a max value used for plotting. Otherwise use the highest q50 value.
        '''
    
        print 'Reading in Observed File...'
        
        if Obs_Label==None and Pred_Label == None:
            inputs = self.get_inputs('PVO')
            Obs_Label = inputs['PVO_Obs_Label']
            Pred_Label = inputs['PVO_Pred_Label']
            self.Map_Utils.title_str = inputs['PVO_Title']

        Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                                       self.Cohorts, self.Surveys)
        Obs_data_Manager.InitializeData(Obs_data_file, datatype='observed', Label=Obs_Label)
        print 'Reading in Predicted Data'
        Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                                       self.Cohorts, self.Surveys)
        Pred_data_Manager.InitializeData(Pred_data_file, datatype='predicted', Label=Pred_Label)
        
        self.Cohorts = Pred_data_Manager.get_Cohorts(self.Cohorts)
        
        for i, cohort in enumerate(self.Cohorts):
            print 'Creating Plot for Cohort {0}...'.format(cohort)

            Obs_data = Obs_data_Manager.get_DataFrame(cohort=cohort)
            Pred_data = Pred_data_Manager.get_DataFrame(cohort=cohort)
            dataframe = Pred_data_Manager.Coordinate_Data(Pred_data, Obs_data)
            dataframe = Pred_data_Manager.Filter_by_HatchDate(dataframe)
            self.Map_Utils.plot_ObsVsPred_Boxwhisker(dataframe, Var, Chronological, cohort, Log, Fishtype, max=max)
            self.Map_Utils.savePlot(Var, self.output_directory)
            
    def make_MultiPredvsObs_BoxWhisker(self,
                                  Obs_data_file,
                                  Pred_data_list,
                                  Var,
                                  Chronological=False,
                                  Log=False,
                                  max=0.,
                                  Fishtype='Longfin Smelt',
                                  Obs_Label=None,
                                  Pred_Labels=None):
        '''
        Creates boxwhisker plots for properly set up data. Instead of coming from trawl observed data,
        data is post processed into csv files containing the q5, q25, q50, q75, and q95 (q meaning quantile)
        statistics. These values are used for creating boxwhisker plots.
        q5 = 5% quantile, bottom whisker
        q25 = 25% quantile, bottom of the box
        q50 = 50% quantile, middle of the box
        q75 = 75% quantile, top of the box
        q95 = 95% quantile, top whisker
        
        Plots multiple predicted data vs a single observed record. 
        This plot can be very busy with too many groups.
        
        The Data acts as a direct comparison of Observed data from collected surveys to computed values.
        
        variable controls including chronological and Log scaling. If Chronological, user must include a pairing trawl csv file that contains
        dates for each survey and region.
        
        Inputs:
        Observed_Data_Dir: path to directory where observed data exists.
        Predicted_Data_Dir: path to directory where predicted data exists.
        Obs_data_list: list of observed data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Pred_data_list: list of Predicted data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        Chronological_data: list set of data to correspond with the trawl data. Only needed if Chronological is passed in as True
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        Max: set a max value used for plotting. Otherwise use the highest q50 value.
        '''
        
        if Obs_Label==None and Pred_Labels == None:
            inputs = self.get_inputs('MULTI')
            Obs_Label = inputs['MULTI_Obs_Label']
            Pred_Labels = inputs['MULTI_Pred_Label']
            self.Map_Utils.title_str = inputs['MULTI_Title']

        
        print 'Reading in Observed File...'
 
        
        Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                                       self.Cohorts, self.Surveys)
        Obs_data_Manager.InitializeData(Obs_data_file, datatype='observed', Label=Obs_Label)
        print 'Reading in Predicted Data'
        Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                                       self.Cohorts, self.Surveys)
        Pred_data_Manager.InitializeData(Pred_data_list, datatype='predicted', Label=Pred_Labels)
        
        self.Cohorts = Pred_data_Manager.get_Cohorts(self.Cohorts)
        
        for i, cohort in enumerate(self.Cohorts):
            print 'Creating Plot for Cohort {0}...'.format(cohort)
            Obs_data = Obs_data_Manager.get_DataFrame(cohort=cohort)
            Pred_data = Pred_data_Manager.get_DataFrame(cohort=cohort)
            dataframe = Pred_data_Manager.Coordinate_Data(Pred_data, Obs_data)
            dataframe = Pred_data_Manager.Filter_by_HatchDate(dataframe)
            self.Map_Utils.plot_MultiObsVsPred_Boxwhisker(dataframe, Var, Chronological, cohort, Log, Fishtype, datatype='multi', max=max)
            self.Map_Utils.savePlot(Var)


    def make_TotalPredvsObs_BoxWhisker(self,
                                       Obs_data_file,
                                       Pred_data_file,
                                       Var,
                                       Chronological=False,
                                       Log=False,
                                       max=0.,
                                       Fishtype='Longfin Smelt',
                                       Obs_Label=None,
                                       Pred_Label=None):                            
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
        Observed_Data_Dir: path to directory where observed data exists.
        Predicted_Data_Dir: path to directory where predicted data exists.
        Obs_data_list: list of observed data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Pred_data_list: list of Predicted data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        Chronological_data: list set of data to correspond with the trawl data. Only needed if Chronological is passed in as True
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        Max: set a max value used for plotting. Otherwise use the highest q50 value.        
        '''
        
        if Obs_Label==None and Pred_Label == None:
            inputs = self.get_inputs('TPVTO')
            Obs_Label = inputs['TPVTO_Obs_Label']
            Pred_Label = inputs['TPVTO_Pred_Label']
            self.Map_Utils.title_str = inputs['TPVTO_Title']
        
        print 'Reading in Observed File...'

        Obs_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                                       self.Cohorts, self.Surveys)
        Obs_data_Manager.InitializeData(Obs_data_file, datatype='total_observed', Label=Obs_Label)
        print 'Reading in Predicted Data'
        Pred_data_Manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                                       self.Cohorts, self.Surveys)
        Pred_data_Manager.InitializeData(Pred_data_file, datatype='total_predicted', Label=Pred_Label)
    
        print self.Surveys
        Obs_data = Obs_data_Manager.get_DataFrame()
        Pred_data = Pred_data_Manager.get_DataFrame()
        dataframe = Pred_data_Manager.Coordinate_Data(Pred_data, Obs_data)
        dataframe = Pred_data_Manager.Filter_by_HatchDate(dataframe)
        self.Map_Utils.plot_ObsVsPred_Boxwhisker(dataframe, Var, Chronological, 'Total', Log, Fishtype, max=max)
        self.Map_Utils.savePlot(Var)
        
        
    def make_Cohort_BoxWhisker(self,
                              Data_dir,
                              data_files,
                              Var,
                              Log=False,
                              datatype=None,
                              max=0.,
                              Fishtype='Longfin Smelt'):
        '''
        UNDER CONSTRUCTION DO NOT USE
        
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
        Data_Dir: path to directory where data exists.
        data_files: list of data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        Chronological_data: list set of data to correspond with the trawl data. Only needed if Chronological is passed in as True
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        Cohorts: number of cohorts to use. Maybe use list of data sources?
        Max: set a max value used for plotting. Otherwise use the highest q50 value.
        '''
#         cohorts = self.Surveys
        for i, cohort_file in enumerate(data_files):
            cohort = i+1
            print 'Creating Plot for Cohort {0}...'.format(cohort)
            self.Groups = range(cohort, self.Groups[-1]+1)
            bw_data = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                                  self.Groups, self.Group_Type)
            Trawl_Data = os.path.join(Data_dir, cohort_file)
            bw_data.InitializeData(Trawl_Data)
            data = bw_data.get_DataFrame()
            self.Map_Utils.plot_boxwhisker(data, Var, '', Log, Fishtype, datatype=datatype, cohortNum=cohort, max=max)
            self.Map_Utils.savePlot(Var)


    def make_TimeSeries_Plots(self,
                              Datafile,
                              Var,
                              Log=False,
                              datatype='fractional_entrainment',
                              max=0.,
                              Fishtype='Longfin Smelt'):
        '''
        Creates a timeseries plot for properly set up data. At each location, cohort data is displayed over time. 
        Each cohort is represented as a line of varying color. The x axis represents time, while the y axis
        represents the variable. Areas with no data are not given a plot.
        
        datafile is traditionally set up with columns being 'REGION_COHORT', and days since hatching.
        
        Inputs:
        Datafile: full path to file containing data for the time series
        Var: plot type variable. Abundance or Density
        Log: when passed in true, use a log scale to plot. False by default. 
        datatype: used to specify different type of data. set to 'fractional_entrainment' by default.
                  fractional_entrainment is used if the data values are percents (i.e. 0-1)
                  more datatypes available at a later date.
        Max: set a max value used for plotting. Otherwise use the highest value.
        '''
        data = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'timeseries', '', 
                           self.Groups, self.Group_Type)
        data.InitializeData(Datafile)
        tsdata = data.get_DataFrame()
        date_data = data._get_Timeseries_Dates()
        self.Map_Utils.plot_timeseries(tsdata, Var, date_data, Log, Fishtype, datatype=datatype, max=max)
        self.Map_Utils.savePlot(Var)
        
def make_spotCheck_BoxWhisker(self,
                              datafile,
                              Var,
                              cohorts,
                              Log=False,
                              datatype=None,
                              max=0.,
                              Fishtype='Longfin Smelt'):
        '''
        UNDER CONSTRUCTION DO NOT USE
        
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
        Data_Dir: path to directory where data exists.
        data_files: list of data file names. Include full name.
                        example: ['test1.csv', 'test2.csv']
        Var: plot type variable. Abundance or Density
        Chronological: Boolean to turn on Chronological plotting.
                       If True, bars are ordered by the survey date, not the load order
        Chronological_data: list set of data to correspond with the trawl data. Only needed if Chronological is passed in as True
        Log: Plots data with a log scale instead of a true scale. Can make data with a large variation easier to view. 
        Cohorts: number of cohorts to use. Maybe use list of data sources?
        Max: set a max value used for plotting. Otherwise use the highest q50 value.
        '''
#         cohorts = self.Surveys

        for i, cohort in enumerate(cohorts):
#             self.Groups = range(i+1, self.Groups[-1]+1)
            data_manager = DataManager(self.Map_Utils.poly_names, self.Year, self.Sizes, 'Boxwhisker', '', 
                               self.Groups, self.Group_Type)
            data_manager.InitializeData(datafile, datatype=datatype)
            data = data_manager.get_DataFrame()
            self.Map_Utils.plot_boxwhisker(data, Var, '', Log, Fishtype, datatype=datatype, cohortNum=cohort, max=max)
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
    hatch = False
    entrainment = False
    PredvsMultiObs = False
    CohortBW = False #UNDER CONSTRUCTION
    EntrainmentTS = False
    spotCheck = True
    
    if bar:
#         Var = 'Density'
        Var = 'Abundance'
        trawl_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"]
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        
        sizes = [6, 10]
        surveys = [[3,4,5,6], [1,2,3,4,5,6,7,8,9]]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
         
        lfp.make_Bars(trawl_data,static_volumes, Var, GrowthRate=0.2, Chronological=False, Log=True)
        
    if box:
        Var = 'Abundance'
        trawl_data = [r"J:\Longfin\bar_plots\SLS_quantiles_12mm-16mm_2012-3-1_grow0.30_2012.csv", r"J:\Longfin\from_Ed\20mm_quantiles_12mm-16mm_2012-3-1_grow0.20_2012.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv", r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"]
        sizes = [12,16]
        surveys = [[1,2,3,4,5,6], [1,2,3,4,5,6,7,8,9]]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
         
        lfp.make_BoxWhisker(trawl_data, Var, Chronological=True, Chronological_data=Chron_data, Log=True)
        
    if pvo_boxw:
        Var = 'Abundance'
        Pred_data_dir = r"C:\git\longfin_trawl_map\4-16-2019\Test"
        Obs_data_dir = r"C:\git\longfin_trawl_map\4-16-2019\Test"
#         Pred_data = ["quantiles_1.csv",
#                      "quantiles_2.csv",
#                      "quantiles_3.csv",
#                      "quantiles_4.csv",
#                      "quantiles_5.csv",
#                      "quantiles_6.csv"]
        Pred_data = ['quantiles.csv']
        Obs_data  = ["Test_quantiles_4mm-7mm_2012-12-13_grow0.20_2013.csv",
                     "Test_quantiles_4mm-7mm_2012-12-28_grow0.20_2013.csv",
                     "Test_quantiles_4mm-7mm_2013-01-12_grow0.20_2013.csv",
                     "Test_quantiles_4mm-7mm_2013-01-27_grow0.20_2013.csv",
                     "Test_quantiles_4mm-7mm_2013-02-11_grow0.20_2013.csv",
                     "Test_quantiles_4mm-7mm_2013-02-26_grow0.20_2013.csv",
                     "Test_quantiles_4mm-7mm_2013-03-13_grow0.20_2013.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [4,7]
        surveys = [1,2,3,4]
        Condensed_Cohorts = [1,2,3,4]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
         
        lfp.make_PredvsObs_BoxWhisker(Obs_data_dir, Pred_data_dir, Obs_data, Pred_data, Chron_data, Var, 
                                      Log=False, datatype='condensed_predicted', Condensed_Cohorts=Condensed_Cohorts)

    if pvo_boxw_Total:
        Var = 'Abundance'
        Pred_data_dir = r"C:\git\longfin_trawl_map\4-16-2019"
        Obs_data_dir = r"C:\git\longfin_trawl_map\4-16-2019"
        Pred_data = ["tot_quantiles.csv"]
        Obs_data = ["SLS_quantiles_3mm-18mm_2013.csv"]
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [3,18]
        surveys = [1,2,3,4,5,6]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
         
        lfp.make_TotalPredvsObs_BoxWhisker(Pred_data_dir, Obs_data_dir, Pred_data, Obs_data, Chron_data, Var, Log=False)
    
    
    if hatch:
        Var = 'Larvae'
        trawl_data = [r"C:\git\longfin_trawl_map\4-16-2019\grow_27\hatch_quantiles.csv"]
        sizes = []
        cohorts = [1,2,3,4,5,6,7]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, cohorts=cohorts)
         
        lfp.make_BoxWhisker(trawl_data, Var, Log=False, datatype='hatch', max=5000000000.)
        
    if entrainment:
        Var = 'Larvae'
        trawl_data = [r"C:\git\longfin_trawl_map\4-16-2019\grow_27\entrainment_quantiles.csv"]
        sizes = []
        cohorts = [1,2,3,4,5,6,7]
         
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, cohorts=cohorts)
         
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
        
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
        lfp.make_MultiPredvsObs_BoxWhisker(observed_data_dir, predicted_data_dir, Observed_data, predicted_data, Chron_data, Var, Log=True)
         
    if CohortBW:
        '''
        UNDER CONSTRUCTION
        '''
        Obs_data_dir = r"C:\git\longfin_trawl_map\4-16-2019"
        observed_data = ["20mm_quantiles_3mm-18mm_2013.csv"]
        Var = 'Abundance'
        Chron_data = [r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"]
        sizes = [4,7]
        surveys = [1,2,3,4,5,6,7]
        cohorts = [1,2,3,4,5]
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, surveys=surveys)
         
        lfp.make_Cohort_BoxWhisker(Obs_data_dir, observed_data, Var, Log=True)
        
    if EntrainmentTS:
        Var = 'Larvae'
        sizes=[]
        cohorts = [1,2,3,4,5,6]
        entrainment_files = r"C:\git\longfin_trawl_map\4-16-2019\proportional_entrainment.csv"
        lfp = LongfinPlotter(run_dir, grd_file, year, sizes, cohorts=cohorts)
        lfp.make_TimeSeries_Plots(entrainment_files, Var, datatype='fractional_entrainment', max=1.)
                             
    if spotCheck:
        var = 'abundance'
        surveys = [1,2,3,4,5,6]
        cohorts = [1,2,3,4,5,6,7]
        observed_file = r"C:\git\longfin_trawl_map\5-16-2019\observed_cohort_abundance_quantiles.csv"
        lfp = LongfinPlotter(run_dir, grd_file, year, [], surveys=surveys)
        lfp.make_spotCheck_BoxWhisker(observed_file, Var, datatype='Observed', cohorts=cohorts)
