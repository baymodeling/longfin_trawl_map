'''
Created on Feb 14, 2019

@author: scott
'''

import os, sys
import pandas as pd
import numpy as np
import datetime as dt
import math
    
class DataManager(object):
    '''
    Class to handle Trawl data. Each Trawl data is paired with a static volume file in 
    order to calculate different Metrics.
    Included must be a list of regions.
    '''
    def __init__(self,
                 regions,
                 Year,
                 Sizes,
                 Surveys,
                 DataSourceType,
                 static_volume_file,
                 startDate=dt.datetime(2019,1,1)):
        
        
        self.regions = regions
        if static_volume_file != '':
            self._read_Static_Volumes(static_volume_file)
        self.Year = Year
        self.Sizes = Sizes
        self.Surveys = Surveys
        self.plottype = DataSourceType.lower()
        self.startDate = startDate
        self._initialize_DataFrame()
        
    def _initialize_DataFrame(self):
        '''
        Creates the main dataframe object based on run type.
        '''
        if self.plottype == 'bar':
            self.mainDataFrame = pd.DataFrame(columns=['Region', 'Survey', 'StartDate', 'Source', 'LoadOrder', 'Abundance', 'Density'])
        elif self.plottype == 'boxwhisker':
            self.mainDataFrame = pd.DataFrame(columns=['Region', 'Survey', 'Source', 'LoadOrder', 'q5', 'q25', 'q50', 'q75', 'q95']) 
        elif self.plottype == 'timeseries':
            self.mainDataFrame = pd.DataFrame(columns=['Region', 'Survey', 'Source', 'LoadOrder', 'Values', 'Days'])
        print 'Main Data Frame initialized...'
        
    def _append_mainDataframe(self, **kwargs):
        '''
        Appends the main data frame with new data for a different region/survey
        Data is highly dependent on what is passed in.
        '''
        if self.plottype == 'bar':
            self.mainDataFrame = self.mainDataFrame.append({'Region': kwargs['Region'],
                                                            'Survey': kwargs['Survey'],
                                                            'StartDate': kwargs['StartDate'],
                                                            'Source': kwargs['Source'], 
                                                            'LoadOrder': kwargs['LoadOrder'],
                                                            'Abundance': kwargs['Abundance'], 
                                                            'Density': kwargs['Density']},
                                                            ignore_index=True)
        elif self.plottype == 'boxwhisker':
            self.mainDataFrame = self.mainDataFrame.append({'Region': kwargs['Region'],
                                                            'Survey': kwargs['Survey'],
                                                            'Source': kwargs['Source'],
                                                            'LoadOrder': kwargs['LoadOrder'],
                                                            'q5': kwargs['q5'], 
                                                            'q25': kwargs['q25'], 
                                                            'q50': kwargs['q50'], 
                                                            'q75': kwargs['q75'], 
                                                            'q95': kwargs['q95']}, 
                                                            ignore_index=True)
        elif self.plottype == 'timeseries':
            self.mainDataFrame = self.mainDataFrame.append({'Region': kwargs['Region'],
                                                            'Survey': kwargs['Survey'],
                                                            'Source': kwargs['Source'],
                                                            'LoadOrder': kwargs['LoadOrder'],
                                                            'Values': kwargs['Values']}, 
                                                            ignore_index=True)
            
        print 'Main Data Frame Appended with Region {0} Survey {1} from {2}'.format(kwargs['Region'], kwargs['Survey'], kwargs['Source'])
        
    def _update_mainDataframe(self, row_number, UpdateDict):
        '''
        Updates a main dataframe value
        '''
        for update_key in UpdateDict.keys():
            if self.mainDataFrame[update_key][row_number] != UpdateDict[update_key]:
                print 'Updating {0} Survey {1} {2} from {3} to {4}'.format(self.mainDataFrame['Region'][row_number], self.mainDataFrame['Survey'][row_number], update_key, self.mainDataFrame[update_key][row_number], UpdateDict[update_key])
#             self.mainDataFrame[update_key][row_number] = UpdateDict[update_key] #chaining warning
            self.mainDataFrame.ix[row_number,update_key] = UpdateDict[update_key]
            
    def _merge_with_mainDataFrame(self, dataframe):
        self.mainDataFrame = pd.concat([self.mainDataFrame, dataframe])
        print 'Main Dataframe appended'
        
            
    def _read_Trawl_Data(self, Data_file):
        '''
        Reads in the trawl csv file and makes it a class object through pandas
        '''
        self.Trawl_Data = pd.read_csv(Data_file, parse_dates=True)
        return
        
    def _read_Static_Volumes(self, static_volume_file):
        '''
        Reads in the static Volumes csv file and makes it a class object through pandas.
        Also creates a dictionary object that corresponds with each region and volume
        '''
        df = pd.read_csv(static_volume_file, parse_dates=True)
        self.static_volumes = {}
        for i, region in enumerate(df['region_name'].values):
            self.static_volumes[region.replace(' ', '_')] = df['vol_top_999_m'][i]
        return
    
    def _get_Valid_Idx(self, Key, DataField, Filter=None, contain=False):
        '''
        Gathers all the correct indexes for a trawl data file for a determined column and key.
        For example, gathers all index for Region Napa Sonoma
        Filter allows the user to pass in existing filtered indexes in the form of a list.
        The code will then choose cells that meet both list criteria, so that the user can
        combine two lists that include, for example, year 2012 and region Napa Sonoma
        Not entering a filter will parse all values.
        
        Key: Value checked for in each row in a specific column, e.g., 2012, Napa Sonoma
        DataField: Column header from CSV pandas dataframe object to search in, e.g. Region, Year
        Filter: existing list of indexes from a previously filtered list. 
        
        returns list of indexes in Trawl Data csv that meets criteria
        '''
        if contain:
            print Key
            valid_Idx = [r for r, value in enumerate(self.Trawl_Data.columns.values) if str(Key) in value]
            if Filter != None and type(Filter) == list:
                valid_Idx = list(set(valid_Idx).intersection(Filter))
            
            if len(valid_Idx) == 0:
                print 'ERROR in Trawl Data. Field {0} not found in headers.'.format(Key)
                
        else:
            if DataField not in self.Trawl_Data.columns:
                print 'ERROR in Trawl Data. Field {0} not found in headers.'.format(DataField)
                print 'Ensure Trawl Data has proper headers and restart.'
                sys.exit(0)
                
            valid_Idx = [r for r, value in enumerate(self.Trawl_Data[DataField].values) if value == Key]
            if Filter != None and type(Filter) == list:
                valid_Idx = list(set(valid_Idx).intersection(Filter))
            
        return valid_Idx
    
    def _sum_Idx_Values(self, Idxs, column):
        '''
        Sums all values of a specific column for specific idxs
        '''
        total = 0
        for idx in Idxs:
            total += self.Trawl_Data[column].values[idx]
        return total
            
        
    def _get_Fish_Size_Counts(self, Indexes, Sizes):
        '''
        Adds together all fish counts within a specified size range. 
        Size range comes in a list of two values, a min and a max that is inclusive.
        '''
        if Sizes == [0,0]:
            size_ranges = range(self.Sizes[0], self.Sizes[1]+1)
        else:
            size_ranges = range(Sizes[0], Sizes[1]+1)
        total_count = 0
        for size in size_ranges:
            
            Size_Column_Name = str(size) + 'mm'
            total_count += self._sum_Idx_Values(Indexes, Size_Column_Name)
            
        return total_count
    
    def _get_Fish_Volumes(self, Idxs):
        '''
        Sums up all volumes in a set of dataset indexes
        returns a single value
        '''
        total_volume = self._sum_Idx_Values(Idxs, 'Volume')
            
        return total_volume

    def _checkforHeader(self, header):
        '''
        checks and make sure datasets have correctly named 
        If the header cannot be found, the user may manually enter a new one
        '''
        if header not in self.Trawl_Data.columns:   
            while header not in self.Trawl_Data.columns:
                print 'WARNING: Header {0} not found in Trawl Data Columns.'.format(header)
                header = raw_input('Please enter header to be used instead: ')
                
        return header
    
    

    
    def _get_Region_Stats(self, Region, Survey, Sizes=[0,0], datatype=None):     
        '''
        For a specific dataset, finds and calculates the density and abundance and starttime of 
        a specific region and survey
        '''
        if self.plottype == 'bar':
            region_idx = self._get_Valid_Idx(Region, 'lfs_region')
            Survey_Idx = self._get_Valid_Idx(Survey, 'Survey', Filter=region_idx)
            valid_idx = self._get_Valid_Idx(self.Year, 'Year', Filter=Survey_Idx)
            valid_idx = self._filter_by_StartDate(valid_idx)
            StartDate = self.get_StartDate(Region, Survey)
            Survey_Count = self._get_Fish_Size_Counts(valid_idx, Sizes)
            Survey_Volume = self._get_Fish_Volumes(valid_idx)
            if len(valid_idx) == 0:
                return -1., -1., StartDate
            Region_Density = Survey_Count / Survey_Volume
            static_vol = self.static_volumes[Region]
#             Region_Abundance = np.nan_to_num(Region_Density * static_vol)
            Region_Abundance = Region_Density * static_vol
            
            return Region_Abundance, Region_Density, StartDate
        
        elif self.plottype == 'boxwhisker':
            if datatype in ['predicted', 'multipredicted']:
                valid_headers = [n for n in self.Trawl_Data.columns.values if Region in n]
                region_df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Day', 'Source'})
                
                for index, row in self.Trawl_Data.iterrows():
                    try:
                        date_string = dt.datetime(1970,1,1) + dt.timedelta(days=int(row['date_string']))
                    except KeyError:
                        date_string = dt.datetime(1970,1,1)
                        
#                         
                    region_df = region_df.append({'Region':Region,
                                                  'Day':date_string},
                                                  ignore_index=True)
                    
                    for header in valid_headers:
                        quantile = 'q' + str(header.split('_')[-1])
                        region_df.ix[index, quantile] = row[header]
                        
                return region_df
            
            elif datatype in ['hatch', 'entrainment']:
                valid_headers = [n for n in self.Trawl_Data.columns.values if Region in n]
                region_df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Cohort', 'Source'})
                
                for index, row in self.Trawl_Data.iterrows():
                    cohort = row['cohort']
                        
#                         
                    region_df = region_df.append({'Region':Region,
                                                  'Cohort':cohort},
                                                  ignore_index=True)
                    
                    for header in valid_headers:
                        quantile = 'q' + str(header.split('_')[-1])
                        region_df.ix[index, quantile] = row[header]
                        
                return region_df
            
            elif datatype in ['condensed_predicted']:
                valid_headers = [n for n in self.Trawl_Data.columns.values if Region in n]
#                 valid_headers = [n for n in valid_headers if n.split('_')[-2] == str(Survey)]
                region_df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Day', 'Source', 'Cohort'})
                
                for index, row in self.Trawl_Data.iterrows():
                    try:
                        date_string = dt.datetime(1970,1,1) + dt.timedelta(days=int(row['date_string']))
                    except KeyError:
                        date_string = dt.datetime(1970,1,1)
                        
#                         
                    
                    header_lib = {}
                    for header in valid_headers:
                        cohort =  str(header.split('_')[-2])
                        if cohort not in header_lib.keys():
                            header_lib[cohort] = {}
                        quantile = 'q' + str(header.split('_')[-1])
                        header_lib[cohort][quantile] = row[header]
                        
                    for cohort in header_lib.keys():
                        region_df = region_df.append({'Region':Region,
                                                  'Day':date_string,
                                                  'Cohort': int(cohort),
                                                  'q5': header_lib[cohort]['q5'], 
                                                  'q25': header_lib[cohort]['q25'],
                                                  'q50': header_lib[cohort]['q50'],
                                                  'q75': header_lib[cohort]['q75'],
                                                  'q95': header_lib[cohort]['q95']},
                                                  ignore_index=True)
#                         for quantile in header_lib[cohort]:
#                             region_df.ix[index, quantile] = row[header]
                        
                        
                
                    
                        
                return region_df
            
            
            elif datatype == None:
                region_idx = self._get_Valid_Idx(Region.replace('_', ' '), 'region')
                Survey_Idx = self._get_Valid_Idx(Survey, 'survey', Filter=region_idx)
                if len(Survey_Idx) > 1:
                    print 'Multiple Entries for {0} for {1} {2}. Please check data inputs and try again.'.format(self.plottype, Region, Survey)
                    print 'Now exiting...'
                    sys.exit(0)
                elif len(Survey_Idx) == 0:
                    print 'No data found for {0} {1}'.format(Region, Survey)
                    return -1.,-1.,-1.,-1.,-1.
                Survey_Idx = Survey_Idx[0]
                q5,q25,q50,q75,q95 = self._get_BoxWhisker_Stats(Survey_Idx)
                return q5,q25,q50,q75,q95
            
        elif self.plottype == 'timeseries':
            region_idx = self._get_Valid_Idx(Region, 'region', contain=True)
            Survey_Idx = self._get_Valid_Idx(Survey, 'Survey', Filter=region_idx, contain=True)
            region_df = pd.DataFrame(columns={'Region', 'Data', 'Survey', 'Source'})    
                
            for i, (label, content) in enumerate(self.Trawl_Data.iteritems()):
                if i in Survey_Idx:
                    region = '_'.join(label.split('_')[:-1])
                    survey = label.split('_')[-1]
                    data = content.tolist()
                    
                    return data
                    
                
            
        
    def _get_BoxWhisker_Stats(self, idx):
        '''
        Sorts and grabs boxwhisker stats from file.
        '''
        
        q5 = self.Trawl_Data['q5'][idx] 
        q25 = self.Trawl_Data['q25'][idx] 
        q50 = self.Trawl_Data['q50'][idx] 
        q75 = self.Trawl_Data['q75'][idx] 
        q95 = self.Trawl_Data['q95'][idx]
        
        return q5,q25,q50,q75,q95
        
    
    def _get_Timeseries_Dates(self): 
            
        converted_datestr = []
        for date in self.Trawl_Data['date_string'].tolist():
            try:
                date_string = dt.datetime(1970,1,1) + dt.timedelta(days=int(date))
            except KeyError:
                date_string = dt.datetime(1970,1,1)
            converted_datestr.append(date_string)
        
        return converted_datestr

   
    def _check_surveyLength(self, len_DataSources, Surveys):   
        '''
        checks the length of the input surveys. Normally, a list of surveys and list of data sources
        are input, such as...
        [source1, source2]
        [[survey set 1], [survey set 2]]
        Matching source 1 with survey set 1, and source 2 with survey set 2
        if there are a mismatch of survey sets and sources, the dataframe is adjusted to fix that.
        '''
        if type(Surveys) == list:
            if type(Surveys[0]) != list:
                if len_DataSources > 1:
                    print 'Found Multiple Datasets but only defined one set of Surveys.'
                    print 'Using the same set of Surveys for all Datasets.'
                    new_surveys = []
                    for i in range(len_DataSources):
                        new_surveys.append(Surveys)
                    return new_surveys
                else:
                    return [Surveys]
            else:
                return Surveys
        
    def _filter_by_StartDate(self, validIdx):
        '''
        takes a dataset and removes all data that 
        '''
        new_validIdx = []
        dateheader = self._checkforHeader('SampleDate')
        for idx in validIdx:
            curDate = dt.datetime.strptime(self.Trawl_Data[dateheader].values[idx], '%m/%d/%Y %H:%M')
            if curDate > self.startDate:
                new_validIdx.append(idx)

        return new_validIdx
    

        
    
    def _calculate_Sizes_with_Growth(self, dataframe, GrowthRate):
        '''
        Calculates how much growth is needed to be added judging by the survey date
        '''
        calculated_sizes = []
        for index, row in dataframe.iterrows():
            if row.name == dataframe.iloc[0].name:
                calculated_sizes.append(self.Sizes)
                start_date = row['StartDate']
            else:
                time_elapsed = row['StartDate'] - start_date
                if time_elapsed.days < 365:
                    growth = time_elapsed.days * GrowthRate
                    growth_rounded = int(math.ceil(growth))
                    calculated_sizes.append([self.Sizes[0] + growth_rounded, self.Sizes[1] + growth_rounded])
                else:
                    print 'Time between Surveys longer than a year. Assuming no data.'
                    calculated_sizes.append([self.Sizes[0], self.Sizes[1]])
            
        return calculated_sizes
    
    def _get_Unique_Surveys(self, DataFrame):
        '''
        Gets the number of unique surveys in a dataset for legend plotting
        '''
    
        counted_Surveys = []
        for index, row in DataFrame.iterrows():
            survey = row['Survey']
            source = row['Source']
            SurvSource = (survey, source)
            if SurvSource not in counted_Surveys:
                counted_Surveys.append(SurvSource)
                
        return counted_Surveys

    def _get_Correct_Pred_Sources(self, Survey, Pred_List):
        '''
        Grabs the list of predicted data and organzies them based on Survey number for Total Cohort plots.
        Survey 3 uses quantiles, 1, 2 and 3, Survey 5 uses 1,2,3,4,5, etc...
        HEAVILY depends on pred data named quantiles_x or tot_quantiles
        '''
        new_pred_list = []
        for Pred_source in Pred_List:
            if Pred_source.split('_')[0].lower() == 'tot':
                new_pred_list.append(Pred_source)
            else:
                try:
                    if float(Pred_source.split('_')[1]) <= Survey:
                        new_pred_list.append(Pred_source)
                except:
                    print 'Unknown file name for predicted data:', Pred_source
                    checkadd = raw_input('Include {0} for Survey {1}? (Y/N)'.format(Pred_source, Survey)) 
                    while checkadd.lower() not in ['y', 'n']:
                        print 'Input {0} not understood. Please use Y or N to respond.'.format(checkadd)
                        checkadd = raw_input('Include {0} for Survey {1}? (Y/N)'.format(Pred_source, Survey)) 
                    if checkadd.lower() == 'y':
                        print 'Using {0} for Survey {1}'.format(Pred_source, Survey)
                        new_pred_list.append(Pred_source)
                    elif checkadd.lower() == 'n':
                        print 'Not using {0} for Survey {1}'.format(Pred_source, Survey)
                    else:
                        print 'You should never be here. Begone.'
                    
        return new_pred_list
    
    def _get_Survey_Order(self, dataframe):
        '''
        Creates a new dataframe that identifies the start date for each Survey and source, and then sorts
        that data based on the start date for chronological plots.
        '''
        
        Survey_Order = pd.DataFrame(columns=['Survey', 'Source', 'StartDate'])
        Surveys = self._get_Unique_Surveys(dataframe)
        for SurvSource in Surveys:
            FiltData = dataframe.loc[dataframe['Survey'] == SurvSource[0]]
            FiltData = FiltData.loc[FiltData['Source'] == SurvSource[1]]
            earliest_Date = min([r for r in FiltData['StartDate'].values])
            Survey_Order = Survey_Order.append({'Survey': SurvSource[0], 
                                                'Source': SurvSource[1], 
                                                'StartDate': earliest_Date},
                                                ignore_index=True)
            
        Survey_Order = Survey_Order.sort_values(['StartDate'])
            
        return Survey_Order
    
    
    def _add_PlotOrder(self, Surveys):
        '''
        Adds a plotorder field to the main dataframe, then uses a separate array (generated from 
        _get_Survey_Order()) to determine plot order for chronological plots
        '''
        self.mainDataFrame['PlotOrder'] = 1
        i = 1
        for index, row in Surveys.iterrows():
            update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Survey'] == row['Survey'] and DFrow['Source'] == row['Source']]
            for idx in update_idx:
                self._update_mainDataframe(idx, {'PlotOrder':i})
            i += 1
            
    def _add_Dates(self, Surveys):
        '''
        adds a startdate and enddate field for the maindataframe. Then grabs the corresponding values
        and assigns the correct values.
        '''
        self.mainDataFrame['StartDate'] = ''
        self.mainDataFrame['EndDate'] = ''
        for index, row in Surveys.iterrows():
            update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Survey'] == row['Survey'] and DFrow['Source'] == row['Source'] and DFrow['Region'] == row['Region']]
            for idx in update_idx:
                self._update_mainDataframe(idx, {'StartDate':row['StartDate']})
                self._update_mainDataframe(idx, {'EndDate':row['EndDate']})
                
    def _get_Density_Scalar(self, source):
        '''
        Gets the correct density scalar value for plotting. These values are NOT to be used when calculating abundance.
        SLS and 20mm to be already determined. Unknown sources will only need their values entered once.
        '''
        try:
            self.Density_ID
        except AttributeError:
            self.Density_ID = {}
            
        if 'sls' in source.lower():
            return 1000.
        elif '20mm' in source.lower():
            return 10000.
        elif source.lower() not in self.Density_ID:
            print 'No Density Value for source {0}'.format(os.path.basename(source))
            value = raw_input('Please enter a float Density scalar for new data source: ')
            valaccepted = False
            while not valaccepted:
                try:
                    value = float(value)
                    valaccepted = True
            
                except ValueError:
                    print 'Please enter a float or int value for the density scalar.'
                    value = raw_input('Density Scalar: ')
            
                self.Density_ID[source] = value
            return value      
                        
        

    def _connect_Sources(self, dataframe):
        '''
        Connects two data sources by the source files they use. Dataframe passed in will have it source paths
        changed to match the main dataframe. From there, dataframes can be correctly merged.
        '''
        Source_ID = {}
        for src in self.mainDataFrame['Source'].values:
            if 'sls' in src.lower() and src not in Source_ID.keys():
                Source_ID['sls'] = src
            elif '20mm' in src.lower() and src not in Source_ID.keys():
                Source_ID['20mm'] = src
            elif src.lower() not in Source_ID.keys():
                print 'No identifier for source {0}'.format(os.path.basename(src))
                unknown_ID = raw_input('Please enter a 3 letter ID found in new data source: ')
                Source_ID[unknown_ID] = src
        
        for index,row in dataframe.iterrows():
            Source = row['Source'].lower()
            if 'sls' in Source:
                dataframe.ix[index, 'Source'] = Source_ID['sls']
            elif '20mm' in Source:
                dataframe.ix[index, 'Source'] = Source_ID['20mm']
            elif src not in Source_ID.keys():
                print 'No identifier for source {0}'.format(os.path.basename(src))
                unknown_ID = raw_input('Please enter a data source to be used: ')
                Source_ID[src] = unknown_ID
                
        return dataframe
   
    def _get_Survey_Dates(self, dataFrame, Survey):
        '''
        Gets dates for all trawls for a specific survey, region agnostic. Allows user to get a range of dates
        that a survey may be in in the event that the Trawl data is incomplete.
        Used mostly to get correct data for Predicted data.
        '''
        survey_dates = []
        for index, row in dataFrame.iterrows():
            if row['Survey'] == Survey:
                if row['StartDate'].year == self.Year and row['EndDate'].year == self.Year:
                    survey_dates.append(row['StartDate'])
                    survey_dates.append(row['EndDate'])
        
        try:            
            startDate = min(survey_dates)
        except ValueError:
            startDate = dt.datetime(1900,1,1)
        try:
            endDate = max(survey_dates)
        except:
            endDate = dt.datetime(2100,1,1)
        
        return startDate, endDate
    
    def _get_boxwhisker_Date_values(self, StartDate, EndDate, update_idx):
        '''
        Extracts quantile data from the mainDataFrame for specific dates
        '''
        q5 = []
        q25 = []
        q50 = []
        q75 = []
        q95 = []
        for idx in update_idx:
            if StartDate <= self.mainDataFrame['Day'][idx] <= EndDate:
                q5.append(self.mainDataFrame['q5'][idx])
                q25.append(self.mainDataFrame['q25'][idx])
                q50.append(self.mainDataFrame['q50'][idx])
                q75.append(self.mainDataFrame['q75'][idx])
                q95.append(self.mainDataFrame['q95'][idx])
        return q5, q25, q50, q75, q95
    
    def apply_Chronological(self, Chronological, Chronological_data=[]):
        '''
        Checks to see if the user passed in the Chronological flag.
        If they did, a new dataframe with data for regions, surveys, start dates and sources.
        The new dataframe is sorted by date, and then a plot order is determined.
        This dataframe order is added to the maindataframe and used for plotting.
        '''
        if not Chronological:
            return
        if len(Chronological_data) > 1:
            Chronological_DataFrame = pd.DataFrame(columns=['Region', 'Survey', 'StartDate', 'Source'])
            #check surveys vs num of data sources
            for i, datasource in enumerate(Chronological_data):
                self._read_Trawl_Data(datasource)
                for region in self.regions:
                    for survey in self.Surveys[i]:
                        startDate = self.get_StartDate(region, survey)
                        Chronological_DataFrame = Chronological_DataFrame.append({'Region':region,
                                                                                  'Survey':survey,
                                                                                  'StartDate':startDate,
                                                                                  'Source':datasource},
                                                                                  ignore_index=True)
            
            survey_order = self._get_Survey_Order(Chronological_DataFrame)
            survey_order = self._connect_Sources(survey_order)

            self._add_PlotOrder(survey_order)
        else:
            survey_order = self._get_Survey_Order(self.mainDataFrame)
            self._add_PlotOrder(survey_order)
            
    def addDataset(self, Trawl_Data, Surveys, load_order, datatype=None):
        '''
        Reads in dataset and gets the main data, and then adds it to the master dataframe
        '''
        self._read_Trawl_Data(Trawl_Data)
        
        if datatype in ['predicted', 'multipredicted', 'cohort']:
            for region in self.regions:
                if self.plottype == 'boxwhisker':
                    region_df = self._get_Region_Stats(region, 0, datatype=datatype)
                    region_df['Source'] = os.path.basename(Trawl_Data).split('.')[0]
                    region_df['LoadOrder'] = load_order
                    self._merge_with_mainDataFrame(region_df)
            self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
            
        elif datatype in ['hatch', 'entrainment']:
            for region in self.regions:
                if self.plottype == 'boxwhisker':
                    region_df = self._get_Region_Stats(region, 0, datatype=datatype)
                    region_df['Source'] = os.path.basename(Trawl_Data).split('.')[0]
                    region_df['LoadOrder'] = load_order
                    self._merge_with_mainDataFrame(region_df)
            self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
            
        elif datatype in ['condensed_predicted']:
            for region in self.regions:
#                 for survey in Surveys:
                if self.plottype == 'boxwhisker':
                    region_df = self._get_Region_Stats(region, 0, datatype=datatype)
                    region_df['Source'] = os.path.basename(Trawl_Data).split('.')[0]
                    region_df['LoadOrder'] = load_order
                    self._merge_with_mainDataFrame(region_df)
            self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
            
        elif datatype == None:
            for region in self.regions:
                for survey in Surveys:
                    if self.plottype == 'bar':
                        abundance, density, firstDate = self._get_Region_Stats(region, survey, datatype=datatype)
                        density *= self._get_Density_Scalar(Trawl_Data)
                        self._append_mainDataframe(Region=region, Survey=survey, StartDate=firstDate, LoadOrder=load_order,
                                                   Source=Trawl_Data, Abundance=abundance, Density=density)
                    elif self.plottype == 'boxwhisker':
                        q5, q25, q50, q75, q95 = self._get_Region_Stats(region, survey, datatype=datatype)
                        self._append_mainDataframe(Region=region, Survey=survey, Source=Trawl_Data, LoadOrder=load_order,
                                                   q5=q5, q25=q25, q50=q50, q75=q75, q95=q95)
                    elif self.plottype == 'timeseries':
                        ts_data = self._get_Region_Stats(region, survey, datatype=datatype)
                        self._append_mainDataframe(Region=region, Survey=survey, Source=Trawl_Data, LoadOrder=load_order,
                                                   Values=ts_data)
#             self.mainDataFrame = self.mainDataFrame.append({'Days': date_data}, 
#                                                             ignore_index=True)
                                                   

    def InitializeData(self, Trawl_Data, datatype=None):
        '''
        Takes in a dataset and adds it to the main dataframe
        '''
        
        if type(Trawl_Data) == str:
            len_data = 1
            Trawl_Data = [Trawl_Data]
        elif type(Trawl_Data) == list:
            len_data = len(Trawl_Data)
            
        self.Surveys = self._check_surveyLength(len_data, self.Surveys)
        
        if datatype in ['hatch', 'entrainment', 'multipredicted', 'predicted', 'cohort', 'condensed_predicted']:
            for i, Trawl_data_Source in enumerate(Trawl_Data):
                if self.plottype == 'boxwhisker':
                    self.addDataset(Trawl_data_Source, self.Surveys[i], i, datatype=datatype)
                elif self.plottype == 'bar':
                    print 'Predicted Dataset Bar plots not yet implemented.'
                    print 'Now Exiting...'
                    sys.exit(0)
        
        elif datatype == None: 
            for i, Trawl_data_Source in enumerate(Trawl_Data):
                if self.plottype == 'boxwhisker':
                    self.addDataset(Trawl_data_Source, self.Surveys[i], i)
                elif self.plottype == 'bar':
                    self.addDataset(Trawl_data_Source, self.Surveys[i], i)
                elif self.plottype == 'timeseries':
                    self.addDataset(Trawl_data_Source, self.Surveys[i], i)
                    
        else:
            print 'unknown datatype. Now Exiting...'
            sys.exit(0)
            
        print 'Added {0} Dataset(s)'.format(len(Trawl_Data))
                
    def apply_Growth(self, GrowthRate):
        '''
        Applies growth rate to data.
        As fish grow, the survey size will grow with them (to track a generation)
        Returns sizes needed to plot to track growth overtime.
        Applies to bar plots are boxwhisker will have this calculated
        Updates the dataframe after calculation
        '''
        if GrowthRate > 0.0:
            print 'Applying Growth at a rate of {0} per day'.format(GrowthRate)
            
            self.mainDataFrame= self.mainDataFrame.sort_values(['StartDate'])
            for region in self.regions:
                dataFrame_Filter = self.mainDataFrame.loc[self.mainDataFrame['Region'] == region]
                calculated_sizes = self._calculate_Sizes_with_Growth(dataFrame_Filter, GrowthRate)
                i = 0
                
                source = ''
                for index, row in dataFrame_Filter.iterrows():
                    current_Survey = row['Survey']
                    if source != row['Source']:
                        self._read_Trawl_Data(row['Source']) #make sure you reopen the correct file, else it will use the last file
                    source = row['Source']
                    abundance, density, firstDate = self._get_Region_Stats(region, current_Survey, Sizes=calculated_sizes[i])
                    density *= self._get_Density_Scalar(source)
                    self._update_mainDataframe(index, {'Abundance': abundance, 'Density': density})
                    i += 1
    
    def get_Dates(self, Dataset, startdate=None, obsenddate=None):
        '''
        Creates a new dataframe that keeps track of the region, survey, starttime, endtime, and source.
        reads in the passed in dataframe, then gathers the correct data, and connects the data
        sources. Then adds dates to main dataframe.
        '''
        DataFrame = pd.DataFrame(columns=['Region', 'Survey', 'StartDate', 'EndDate', 'Source'])

        for i, datasource in enumerate(Dataset):
            self._read_Trawl_Data(datasource)
            for region in self.regions:
                    for survey in self.Surveys[i]:
                        if startdate != None:
                            startDate = dt.datetime.strptime(startdate, '%Y-%m-%d')
                        else:
                            startDate = self.get_StartDate(region, survey)
                        if obsenddate != None:
                            endDate = dt.datetime.strptime(startdate, '%Y-%m-%d') + dt.timedelta(days=1)
                        else:
                            endDate = self.get_EndDate(region, survey)
                        DataFrame = DataFrame.append({'Region':region,
                                                      'Survey':survey,
                                                      'StartDate':startDate,
                                                      'EndDate':endDate,
                                                      'Source':datasource},
                                                      ignore_index=True)
        DataFrame = self._connect_Sources(DataFrame)
        self._add_Dates(DataFrame)
            
    def get_Predicted_Timed_Data(self, Observed_Data, datatype=None, cohort=None):   
        '''
        Gets the correct predicted time series data from Computed data excel files. 
        Observed forms give daily values for q5, q25, q50, q75, and q95 regional values.
        By using an observed trawl data file, dates for each region and survey are grabbed.
        Values from the computed file are then averaged over the selected days and returned in a dataframe.
        
        If Total flag is true, Values for each survey are computed by iterating through each 
        observed file. A date for each survey trawl is found. Then each quantiles file before the
        '''  
        Avg_Pred_Df = pd.DataFrame(columns=['Region', 'Survey', 'Source', 'q5', 'q25', 'q50', 'q75', 'q95'])
        for index, row in Observed_Data.iterrows():
            StartDate = row['StartDate']
            EndDate = row['EndDate']
            if StartDate > EndDate:
                StartDate, EndDate = self._get_Survey_Dates(Observed_Data, row['Survey']) ####gets dates for probable survey
            if datatype == 'total':
                Pred_Source_list = list(set(self.mainDataFrame['Source'].tolist())) #gets unique values for a column. Ugly, but effective
                Pred_Source_list = self._get_Correct_Pred_Sources(row['Survey'], Pred_Source_list)
                q5_val = q25_val = q50_val = q75_val = q95_val = 0.
                for current_Source in Pred_Source_list:
                    print 'Getting data from', current_Source, 'Survey', row['Survey'], 'in region', row['Region']
                    update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Region'] == row['Region'] and DFrow['Source'] == current_Source]
                    q5, q25, q50, q75, q95 = self._get_boxwhisker_Date_values(StartDate, EndDate, update_idx)
                    q5_val += np.average(q5) if len(q5) >= 1 else 0.
                    q25_val += np.average(q25) if len(q25) >= 1 else 0.
                    q50_val += np.average(q50) if len(q50) >= 1 else 0.
                    q75_val += np.average(q75) if len(q75) >= 1 else 0.
                    q95_val += np.average(q95) if len(q95) >= 1 else 0.
                
                Avg_Pred_Df = Avg_Pred_Df.append({'Region': row['Region'],
                                                  'Survey': row['Survey'],
                                                  'Source': 'Computed',
                                                  'q5': q5_val,
                                                  'q25': q25_val,
                                                  'q50': q50_val,
                                                  'q75': q75_val,
                                                  'q95': q95_val},
                                                  ignore_index=True)
            elif datatype == 'multipredicted':
                Pred_Source_list = list(set(self.mainDataFrame['Source'].tolist())) #gets unique values for a column. Ugly, but effective
                for source in Pred_Source_list:
                    update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Region'] == row['Region'] and DFrow['Source'] == source]
                    q5, q25, q50, q75, q95 = self._get_boxwhisker_Date_values(StartDate, EndDate, update_idx)
                       
                    Avg_Pred_Df = Avg_Pred_Df.append({'Region': row['Region'],
                                                      'Survey': row['Survey'],
                                                      'Source': source,
                                                      'q5': np.average(q5) if len(q5) >= 1 else 0.,
                                                      'q25': np.average(q25) if len(q25) >= 1 else 0.,
                                                      'q50': np.average(q50) if len(q50) >= 1 else 0.,
                                                      'q75': np.average(q75) if len(q75) >= 1 else 0.,
                                                      'q95': np.average(q95) if len(q95) >= 1 else 0.},
                                                      ignore_index=True)
                
            elif datatype == 'condense_predicted':
                update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Region'] == row['Region'] and DFrow['Cohort'] == cohort]
                q5, q25, q50, q75, q95 = self._get_boxwhisker_Date_values(StartDate, EndDate, update_idx)
                   
                Avg_Pred_Df = Avg_Pred_Df.append({'Region': row['Region'],
                                                  'Survey': row['Survey'],
                                                  'Source': 'Computed',
                                                  'q5': np.average(q5) if len(q5) >= 1 else 0.,
                                                  'q25': np.average(q25) if len(q25) >= 1 else 0.,
                                                  'q50': np.average(q50) if len(q50) >= 1 else 0.,
                                                  'q75': np.average(q75) if len(q75) >= 1 else 0.,
                                                  'q95': np.average(q95) if len(q95) >= 1 else 0.},
                                                  ignore_index=True)                
                
            else:
                update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Region'] == row['Region']]
                q5, q25, q50, q75, q95 = self._get_boxwhisker_Date_values(StartDate, EndDate, update_idx)
                   
                Avg_Pred_Df = Avg_Pred_Df.append({'Region': row['Region'],
                                                  'Survey': row['Survey'],
                                                  'Source': 'Computed',
                                                  'q5': np.average(q5) if len(q5) >= 1 else 0.,
                                                  'q25': np.average(q25) if len(q25) >= 1 else 0.,
                                                  'q50': np.average(q50) if len(q50) >= 1 else 0.,
                                                  'q75': np.average(q75) if len(q75) >= 1 else 0.,
                                                  'q95': np.average(q95) if len(q95) >= 1 else 0.},
                                                  ignore_index=True)                
                
        return Avg_Pred_Df
    
    def get_StartDate(self, Region, Survey):
        '''
        Finds and returns the earliest start date for specific region and survey.
        returns a datetime object
        '''
        Earliest_Survey_Date = dt.datetime(2100,1,1)
        
        dateheader = self._checkforHeader('SampleDate')
        
        region_idx = self._get_Valid_Idx(Region, 'lfs_region')
        Survey_Idx = self._get_Valid_Idx(Survey, 'Survey', Filter=region_idx)
        valid_idx = self._get_Valid_Idx(self.Year, 'Year', Filter=Survey_Idx)
        
        for survey_index in valid_idx:
            current_date = dt.datetime.strptime(self.Trawl_Data[dateheader].values[survey_index], '%m/%d/%Y %H:%M')
            print current_date
            if current_date < Earliest_Survey_Date:
                Earliest_Survey_Date = current_date
                    
        return Earliest_Survey_Date
    
    def get_EndDate(self, Region, Survey):
        '''
        Finds and returns the latest end date for specific region and survey.
        returns a datetime object
        '''
        Latest_Survey_Date = dt.datetime(1900,1,1)
        
        dateheader = self._checkforHeader('SampleDate')
        
        region_idx = self._get_Valid_Idx(Region, 'lfs_region')
        Survey_Idx = self._get_Valid_Idx(Survey, 'Survey', Filter=region_idx)
        valid_idx = self._get_Valid_Idx(self.Year, 'Year', Filter=Survey_Idx)
        
        for survey_index in valid_idx:
            current_date = dt.datetime.strptime(self.Trawl_Data[dateheader].values[survey_index], '%m/%d/%Y %H:%M')
            if current_date > Latest_Survey_Date:
                Latest_Survey_Date = current_date
                    
        return Latest_Survey_Date

    def get_DataFrame(self):
        '''
        returns the current dataframe object
        '''
        return self.mainDataFrame
        
    def correct_Surveys(self, Surveys):
        '''
        removes unused surveys from the mainDataframe. Currently unusued.
        '''
        self.Surveys=[Surveys]
        for index, row in self.mainDataFrame.iterrows():
            if row['Survey'] not in self.Surveys[0]:
                self.mainDataFrame = self.mainDataFrame.drop([index])
                
        self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
    
    def merge_Dataframes(self, dataset1, dataset2):
        '''
        Merges two similar dataframes together and resets the index.
        Columns not shared will be added
        '''
        
        new_dataframe = pd.concat([dataset1, dataset2]).reset_index(drop=True)
        
        return new_dataframe
    
