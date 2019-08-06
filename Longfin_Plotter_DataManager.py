'''
Created on Feb 14, 2019

@author: scott
'''

import os, sys
import pandas as pd
import numpy as np
import datetime as dt
import math
import pdb
    
class DataManager(object):
    '''
    Class to handle data. Each data is paired with a static volume file in 
    order to calculate different Metrics.
    Included must be a list of regions.
    '''
    def __init__(self,
                 regions,
                 Year,
                 Sizes,
                 DataSourceType,
                 static_volume_file,
                 Cohorts,
                 Surveys,
                 startDate=dt.datetime(2019,1,1)
                 ):
        
        
        self.regions = regions
        if static_volume_file != '':
            self._read_Static_Volumes(static_volume_file)
        self.Year = Year
        self.Sizes = Sizes
        self.Cohorts = Cohorts
        self.Surveys = Surveys
        self.plottype = DataSourceType.lower()
        self.startDate = startDate
        self.Source_IDs = {}
        self._initialize_DataFrame()

        
    def _initialize_DataFrame(self):
        '''
        Creates the main dataframe object based on run type.
        '''
        if self.plottype == 'bar':
            self.mainDataFrame = pd.DataFrame(columns=['Region', 'StartDate', 'Source', 'LoadOrder', 'Abundance', 'Density'])
        elif self.plottype == 'boxwhisker':
            self.mainDataFrame = pd.DataFrame(columns=['Region', 'Source', 'LoadOrder', 'q5', 'q25', 'q50', 'q75', 'q95']) 
        elif self.plottype == 'timeseries':
            self.mainDataFrame = pd.DataFrame(columns=['Region', 'Source', 'LoadOrder', 'q5', 'q25', 'q50', 'q75', 'q95']) 
#             self.mainDataFrame = pd.DataFrame(columns=['Region', 'Source', 'LoadOrder', 'Values', 'Days'])
        print 'Main Data Frame initialized...'
        
    def _append_mainDataframe(self, **kwargs):
        '''
        Appends the main data frame with new data for a different region/group
        Data is highly dependent on what is passed in.
        '''
        if self.plottype == 'bar':
            self.mainDataFrame = self.mainDataFrame.append({'Region': kwargs['Region'],
                                                            'StartDate': kwargs['StartDate'],
                                                            'Group': kwargs['Group'],
                                                            'GroupType': kwargs['GroupType'],
                                                            'Source': kwargs['Source'], 
                                                            'LoadOrder': kwargs['LoadOrder'],
                                                            'Abundance': kwargs['Abundance'], 
                                                            'Density': kwargs['Density']},
                                                            ignore_index=True)

        elif self.plottype == 'boxwhisker':
            self.mainDataFrame = self.mainDataFrame.append({'Region': kwargs['Region'],
                                                            'Source': kwargs['Source'],
                                                            'Group': kwargs['Group'],
                                                            'GroupType': kwargs['GroupType'],
                                                            'LoadOrder': kwargs['LoadOrder'],
                                                            'q5': kwargs['q5'], 
                                                            'q25': kwargs['q25'], 
                                                            'q50': kwargs['q50'], 
                                                            'q75': kwargs['q75'], 
                                                            'q95': kwargs['q95']}, 
                                                            ignore_index=True)
        elif self.plottype == 'timeseries':
            self.mainDataFrame = self.mainDataFrame.append({'Region': kwargs['Region'],
                                                            'Source': kwargs['Source'],
                                                            'Group': kwargs['Group'],
                                                            'GroupType': kwargs['GroupType'],
                                                            'LoadOrder': kwargs['LoadOrder'],
                                                            'Values': kwargs['Values']}, 
                                                            ignore_index=True)


        print 'Main Data Frame Appended with Region {0} {1} {2} from {3}'.format(kwargs['Region'], kwargs['GroupType'], kwargs['Group'], kwargs['Source'])
        
    def _update_mainDataFrame(self, row_number, UpdateDict):
        '''
        Updates a main dataframe value
        '''
        for update_key in UpdateDict.keys():
            if self.mainDataFrame[update_key][row_number] != UpdateDict[update_key]:
                if self.mainDataFrame[update_key][row_number] == '':
                    oldval = '[BLANK]'
                else:
                    oldval = self.mainDataFrame[update_key][row_number]
                print 'Updating {0} from {1} to {2}'.format( update_key, oldval, UpdateDict[update_key])
            self.mainDataFrame.ix[row_number,update_key] = UpdateDict[update_key]
            
    def _merge_with_mainDataFrame(self, dataframe):
        '''
        merges a given dataframe with the main dataframe.
        '''
        self.mainDataFrame = pd.concat([self.mainDataFrame, dataframe])
        print 'Main Dataframe appended'
        
    def _read_Data(self, Data_file):
        '''
        Reads in the csv file and makes it a class object through pandas
        '''
        self.Data = pd.read_csv(Data_file)
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
        Gathers all the correct indexes for a data file for a determined column and key.
        For example, gathers all index for Region Napa Sonoma
        Filter allows the user to pass in existing filtered indexes in the form of a list.
        The code will then choose cells that meet both list criteria, so that the user can
        combine two lists that include, for example, year 2012 and region Napa Sonoma
        Not entering a filter will parse all values.
        
        Key: Value checked for in each row in a specific column, e.g., 2012, Napa Sonoma
        DataField: Column header from CSV pandas dataframe object to search in, e.g. Region, Year
        Filter: existing list of indexes from a previously filtered list. 
        contain: instead of checking for exact matches, checks for a string to be in the header
        
        returns list of indexes in Data csv that meets criteria
        '''
        if contain:
            valid_Idx = [r for r, value in enumerate(self.Data.columns.values) if str(Key) in value]
            if Filter != None and type(Filter) == list:
                valid_Idx = list(set(valid_Idx).intersection(Filter))
            
            if len(valid_Idx) == 0:
                print 'ERROR in  Data. Field {0} not found in headers.'.format(Key)
                
        else:
            if DataField not in self.Data.columns: #if the datafield does not exist in the dataset
                try:
                    DataField.lower() in self.Data.columns #try the lowercase first
                except: #if its not, quit and fix.
                    print 'ERROR in Data. Field {0} not found in headers.'.format(DataField)
                    print 'Ensure Data has proper headers and restart.'
                    sys.exit(0)
                else:
                    DataField = DataField.lower() #if its there but lowercase, change input to lowercase
                
            valid_Idx = [r for r, value in enumerate(self.Data[DataField].values) if value == Key]
            if Filter != None and type(Filter) == list:
                valid_Idx = list(set(valid_Idx).intersection(Filter))
            
        return valid_Idx
    
    def _sum_Idx_Values(self, Idxs, column):
        '''
        Sums all values of a specific column for specific idxs
        '''
        total = 0
        for idx in Idxs:
            total += self.Data[column].values[idx]
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
        if header not in self.Data.columns:   
            while header not in self.Data.columns:
                print 'WARNING: Header {0} not found in Data Columns.'.format(header)
                header = raw_input('Please enter header to be used instead: ')
                
        return header
    
    def _get_Region_Stats(self, Region, Survey, datatype=None):     
        '''
        For a specific dataset, finds and calculates the density and abundance and starttime of 
        a specific region and group
        '''
        if self.plottype == 'bar':
            region_idx = self._get_Valid_Idx(Region, 'lfs_region')
            Group_Idx = self._get_Valid_Idx(Group, GroupType, Filter=region_idx)
            valid_idx = self._get_Valid_Idx(self.Year, 'Year', Filter=Group_Idx)
            valid_idx = self._filter_by_StartDate(valid_idx)
            StartDate = self.get_StartDate(Region, Group, GroupType)
            Fish_Count = self._get_Fish_Size_Counts(valid_idx, Sizes)
            Fish_Volume = self._get_Fish_Volumes(valid_idx)
            if len(valid_idx) == 0:
                return -1., -1., StartDate
            Region_Density = Fish_Count / Fish_Volume
            static_vol = self.static_volumes[Region]
#             Region_Abundance = np.nan_to_num(Region_Density * static_vol)
            Region_Abundance = Region_Density * static_vol
            
            return Region_Abundance, Region_Density, StartDate
        
        elif self.plottype == 'boxwhisker':
            if datatype in ['predicted', 'multipredicted']:
                valid_headers = [n for n in self.Data.columns.values if Region in n]
                region_df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Day', 'Source'})
                
                for index, row in self.Data.iterrows():
                    try:
                        date_string = dt.datetime(1970,1,1) + dt.timedelta(days=int(row['date_string']))
                    except KeyError:
                        date_string = dt.datetime(1970,1,1)
                        
#                         
                    region_df = region_df.append({'Region':Region,
                                                  'Day':date_string,
                                                  'GroupType':GroupType},
                                                  ignore_index=True)
                    
                    for header in valid_headers:
                        quantile = 'q' + str(header.split('_')[-1])
                        region_df.ix[index, quantile] = row[header]
                        
                return region_df
            
            elif datatype in ['hatch', 'entrainment']:
                valid_headers = [n for n in self.Data.columns.values if Region in n]
                region_df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Group', 'Source'})
                
                for index, row in self.Data.iterrows():
                    try:
                        group = row[self.GroupType]
                    except KeyError:
                        group = row[self.GroupType.lower()] #sometimes the lowercase is there, by default grouptype is camel case
                    region_df = region_df.append({'Region':Region,
                                                  'Group':group,
                                                  'GroupType':GroupType},
                                                  ignore_index=True)
                    for header in valid_headers:
                        quantile = 'q' + str(header.split('_')[-1])
                        region_df.ix[index, quantile] = row[header]
                        
                return region_df
            
                    
            
            elif datatype in ['condensed_predicted']:
                valid_headers = [n for n in self.Data.columns.values if Region in n]
                region_df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Day', 'Source', 'Group'})
                
                for index, row in self.Data.iterrows():
                    try:
                        date_string = dt.datetime(1970,1,1) + dt.timedelta(days=int(row['date_string']))
                    except KeyError:
                        date_string = dt.datetime(1970,1,1)  
                    
                    header_lib = {}
                    for header in valid_headers:
                        Group =  str(header.split('_')[-2])
                        if Group not in header_lib.keys():
                            header_lib[Group] = {}
                        quantile = 'q' + str(header.split('_')[-1])
                        header_lib[Group][quantile] = row[header]
                        
                    for cohort in header_lib.keys():
                        region_df = region_df.append({'Region':Region,
                                                  'Day':date_string,
                                                  'Group': int(cohort),
                                                  'GroupType':GroupType,
                                                  'q5': header_lib[cohort]['q5'], 
                                                  'q25': header_lib[cohort]['q25'],
                                                  'q50': header_lib[cohort]['q50'],
                                                  'q75': header_lib[cohort]['q75'],
                                                  'q95': header_lib[cohort]['q95']},
                                                  ignore_index=True)                   
                return region_df
            
            
            elif datatype == None:
                region_idx = self._get_Valid_Idx(Region.replace('_', ' '), 'region')
                Group_Idx = self._get_Valid_Idx(Group, GroupType, Filter=region_idx)
                if len(Group_Idx) > 1:
                    print 'Multiple Entries for {0} for {1} {2}. Please check data inputs and try again.'.format(self.plottype, Region, Group)
                    print 'Now exiting...'
                    sys.exit(0)
                elif len(Group_Idx) == 0:
                    print 'No data found for {0} {1}'.format(Region, Group)
                    return -1.,-1.,-1.,-1.,-1.
                Group_Idx = Group_Idx[0]
                q5,q25,q50,q75,q95 = self._get_BoxWhisker_Stats(Group_Idx)
                return q5,q25,q50,q75,q95
            
        elif self.plottype == 'timeseries':
            region_idx = self._get_Valid_Idx(Region, 'region', contain=True)
            Survey_Idx = self._get_Valid_Idx(Survey, Survey, Filter=region_idx, contain=True)

            for i, (label, content) in enumerate(self.Data.iteritems()):
                if i in Survey_Idx:
                    region = '_'.join(label.split('_')[:-1])
                    Survey = label.split('_')[-1]
                    data = content.tolist()
                    
                    return data

    def _get_Stats(self, datatype=None):
        '''
        Gets data from CSV file by going line by line without filtering by date or region. Simpler than _get_Region_stats()
        organizes data into a pandas df
        '''
        
        if datatype in ['observed']:
            df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Survey', 'Date', 'Hatchstart', 'Cohort', 'Samplemean',
                                              'catch', 'CatchMean', 'CatchMin', 'CatchMax', 'Source'})
            
            survey_dates = self.Data.date.unique() #get all survey dates
            survey_dates = [dt.datetime.strptime(n, '%Y-%m-%d') for n in survey_dates] #turn into dt objects
            survey_dates = np.sort(survey_dates) #sort by date
            survey_dates = {x:i+1 for i,x in enumerate(survey_dates)} #make a dict with survey nums
            
            for index, row in self.Data.iterrows():
                if index+1 % 100 == 0:
                    print 'Current line:', index+1
                Date = dt.datetime.strptime(row['date'], '%Y-%m-%d')
                Survey = survey_dates[Date]
                Region = row['region'].replace(' ', '_')
                q5 = row['0.05']
                q25 = row['0.25']
                q50 = row['0.5']
                q75 = row['0.75']
                q95 = row['0.95']
                HatchStart = dt.datetime.strptime(row['hatchstart'], '%Y-%m-%d')
                Cohort = int(row['cohortnum'])
                Samplemean = row['sample_mean']
                Catch = row['catch']
                CatchMean = row['avg']
                CatchMin = row['lmin']
                CatchMax = row['lmax']
                
                df = df.append({'Region':Region, 
                                'q5': q5, 
                                'q25': q25, 
                                'q50': q50, 
                                'q75': q75, 
                                'q95': q95, 
                                'Survey': int(Survey), 
                                'Date': Date, 
                                'Hatchstart': HatchStart, 
                                'Cohort': Cohort, 
                                'Samplemean': Samplemean,
                                'catch': Catch, 
                                'CatchMean': CatchMean, 
                                'CatchMin': CatchMin, 
                                'CatchMax': CatchMax},
                                ignore_index=True)
            return df
        
        elif datatype in ['predicted']:
            df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Hatchstart', 'Date', 'Cohort', 'Samplemean',
                                              'catch', 'CatchMean', 'CatchMin', 'CatchMax', 'Source'})
            
            for index, row in self.Data.iterrows():
                if index+1 % 100 == 0:
                    print 'Current line:', index+1
                Region = row['region'].replace(' ', '_')
                q5 = row['0.05']
                q25 = row['0.25']
                q50 = row['0.5']
                q75 = row['0.75']
                q95 = row['0.95']
                try:
                    Date = dt.datetime.strptime(row['date'], '%Y-%m-%d')
                    HatchStart = dt.datetime.strptime(row['hatchstart'], '%Y-%m-%d')
                except:
                    Date = dt.datetime.strptime(row['date'], '%m/%d/%Y')
                    HatchStart = dt.datetime.strptime(row['hatchstart'], '%m/%d/%Y')
                Cohort = int(row['cohortnum'])
                Samplemean = row['sample_mean']
                Catch = row['catch']
                CatchMean = row['avg']
                CatchMin = row['lmin']
                CatchMax = row['lmax']
                
                df = df.append({'Region':Region, 
                                'q5': q5, 
                                'q25': q25, 
                                'q50': q50, 
                                'q75': q75, 
                                'q95': q95,  
                                'Date': Date, 
                                'Hatchstart': HatchStart, 
                                'Cohort': Cohort, 
                                'Samplemean': Samplemean,
                                'catch': Catch, 
                                'CatchMean': CatchMean, 
                                'CatchMin': CatchMin, 
                                'CatchMax': CatchMax},
                                ignore_index=True)
            return df
        
        elif datatype in ['total_predicted']:
            df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Date', 'Source'})
            
            for index, row in self.Data.iterrows():
                if index+1 % 100 == 0:
                    print 'Current line:', index+1
                Region = row['region'].replace(' ', '_')
                q5 = row['0.05']
                q25 = row['0.25']
                q50 = row['0.5']
                q75 = row['0.75']
                q95 = row['0.95']
                Date = dt.datetime.strptime(row['date'], '%Y-%m-%d')
                
                df = df.append({'Region':Region, 
                                'q5': q5, 
                                'q25': q25, 
                                'q50': q50, 
                                'q75': q75, 
                                'q95': q95,  
                                'Date': Date}, 
                                ignore_index=True)
            return df
                
        elif datatype in ['total_observed']:
            df = pd.DataFrame(columns={'Region', 'Survey', 'q5', 'q25', 'q50', 'q75', 'q95', 'Date', 'Source'})
            
            survey_dates = self.Data.date.unique() #get all survey dates
            survey_dates = [dt.datetime.strptime(n, '%Y-%m-%d') for n in survey_dates] #turn into dt objects
            survey_dates = np.sort(survey_dates) #sort by date
            survey_dates = {x:i+1 for i,x in enumerate(survey_dates)} #make a dict with survey nums
            
            for index, row in self.Data.iterrows():
                if index+1 % 100 == 0:
                    print 'Current line:', index+1
                Date = dt.datetime.strptime(row['date'], '%Y-%m-%d')
                Survey = survey_dates[Date]
                Region = row['region'].replace(' ', '_')
                q5 = row['0.05']
                q25 = row['0.25']
                q50 = row['0.5']
                q75 = row['0.75']
                q95 = row['0.95']
                
                df = df.append({'Region':Region, 
                                'Survey':Survey,
                                'q5': q5, 
                                'q25': q25, 
                                'q50': q50, 
                                'q75': q75, 
                                'q95': q95,  
                                'Date': Date}, 
                                ignore_index=True)
            return df
                
        elif datatype in ['entrainment']:
            df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95', 'Date',
                                       'Source', 'Hatchstart', 'Catch', 'CatchMean', 
                                       'CatchMin', 'CatchMax', 'Samplemean'})
            for index, row in self.Data.iterrows():
                if index+1 % 100 == 0:
                    print 'Current line:', index+1
                Region = row['region'].replace(' ', '_')
                q5 = row['0.05']
                q25 = row['0.25']
                q50 = row['0.5']
                q75 = row['0.75']
                q95 = row['0.95']
                Date = dt.datetime.strptime(row['date'], '%Y-%m-%d')
                HatchStart = dt.datetime.strptime(row['hatchstart'], '%Y-%m-%d')
                Cohort = int(row['cohortnum'])
                Samplemean = row['sample_mean']
                Catch = row['catch']
                CatchMean = row['avg']
                CatchMin = row['lmin']
                CatchMax = row['lmax']
                
                df = df.append({'Region':Region, 
                                'q5': q5, 
                                'q25': q25, 
                                'q50': q50, 
                                'q75': q75, 
                                'q95': q95,  
                                'Date': Date, 
                                'Hatchstart': HatchStart, 
                                'Cohort': Cohort, 
                                'Samplemean': Samplemean,
                                'catch': Catch, 
                                'CatchMean': CatchMean, 
                                'CatchMin': CatchMin, 
                                'CatchMax': CatchMax},
                                ignore_index=True)
            return df
        
        elif datatype in ['hatch']:
            df = pd.DataFrame(columns={'Region', 'q5', 'q25', 'q50', 'q75', 'q95',
                                       'Source', 'Hatchstart', 'Catch', 'CatchMean', 
                                       'CatchMin', 'CatchMax', 'Samplemean'})
            for index, row in self.Data.iterrows():
                if index+1 % 100 == 0:
                    print 'Current line:', index+1
                Region = row['region'].replace(' ', '_')
                q5 = row['0.05']
                q25 = row['0.25']
                q50 = row['0.5']
                q75 = row['0.75']
                q95 = row['0.95']
                HatchStart = dt.datetime.strptime(row['hatchstart'], '%Y-%m-%d')
                Cohort = int(row['cohortnum'])
                Samplemean = row['sample_mean']
                Catch = row['catch']
                CatchMean = row['avg']
                CatchMin = row['lmin']
                CatchMax = row['lmax']
                
                df = df.append({'Region':Region, 
                                'q5': q5, 
                                'q25': q25, 
                                'q50': q50, 
                                'q75': q75, 
                                'q95': q95,  
                                'Hatchstart': HatchStart, 
                                'Cohort': Cohort, 
                                'Samplemean': Samplemean,
                                'catch': Catch, 
                                'CatchMean': CatchMean, 
                                'CatchMin': CatchMin, 
                                'CatchMax': CatchMax},
                                ignore_index=True)
            return df
        
        else:
            print 'Error finding datatype', self.Datatype
            print 'Now exiting...'
            sys.exit(0)

    def _get_BoxWhisker_Stats(self, idx):
        '''
        Sorts and grabs boxwhisker stats from file.
        '''
        
        q5 = self.Data['q5'][idx] 
        q25 = self.Data['q25'][idx] 
        q50 = self.Data['q50'][idx] 
        q75 = self.Data['q75'][idx] 
        q95 = self.Data['q95'][idx]
        
        return q5,q25,q50,q75,q95
        
    
    def _get_Timeseries_Dates(self): 
        '''
        Gets dates from timeseries file and turns them into dt objects
        '''
#         converted_datestr = []
#         for date in self.Data['date_string'].tolist():
#             try:
#                 date_string = dt.datetime(1970,1,1) + dt.timedelta(days=int(date))
#             except KeyError:
#                 date_string = dt.datetime(1970,1,1)
#             converted_datestr.append(date_string)
        total_Dates = []
        dates = self.mainDataFrame.Date.unique()
        for date in dates:
            total_Dates.append(dt.datetime.utcfromtimestamp(date.astype('O')/1e9))
    
        
        return total_Dates
    

    def _getLabels(self):
        if 'Label' not in self.mainDataFrame.columns:
            self.mainDataFrame['Label'] = '' 
        for i, src in enumerate(self.mainDataFrame['Source'].values):
            
            
            if self.mainDataFrame['Label'][i] == '':
                if 'sls' in src.lower() and src not in self.Source_IDs.keys():
                    self.Source_IDs[src] = 'SLS'
                elif '20mm' in src.lower() and src not in self.Source_IDs.keys():
                    self.Source_IDs[src] = '20mm'
                elif src not in self.Source_IDs.keys():
                    print 'No identifier for data source {0}'.format(os.path.basename(src))
                    print 'IDs are used to connect Observed and Predicted data, display chronological data, and display legends. Examples are 20mm and SLS.'
                    print 'This value will be used for the plot legend.'
                    unknown_ID = raw_input('Please enter an ID for new data source: ')
                    self.Source_IDs[src] = unknown_ID
                
                
    def _setLabels(self, Label=None):
        if 'Label' not in self.mainDataFrame.columns:
            self.mainDataFrame['Label'] = '' 
            
#Code to get user input on labels. disabled.
#         if Label != None: 
#             print 'Current Label set for:', Label
#             check_label = raw_input('Use this label? (Y/N): ')
#             while check_label not in ['y','Y', 'N','n']:
#                 print 'Invalid input. Please use Y or N.'
#                 check_label = raw_input('Use this label: {0}? (Y/N): '.format(Label))
#             if check_label.lower() == 'y': 
#                 print 'Label {0} confirmed.'.format(Label)
#             else:
#                 Label = raw_input('Please Enter New Label: ')
        src_un = self.mainDataFrame.Source.unique().tolist()
        for i, src in enumerate(self.mainDataFrame['Source'].values):
            if self.mainDataFrame['Label'][i] == '':
                if Label != None:
                    if type(Label) == list:
                        Li = src_un.index(src)
                        self._update_mainDataFrame(i, {'Label': Label[Li]})
                    else:
                        self._update_mainDataFrame(i, {'Label': Label})
                else:
                    self._update_mainDataFrame(i, {'Label': self.Source_IDs[src]})
                
    def _check_groupingLength(self, len_DataSources, grouping):   
        '''
        groupings can be cohorts or surveys
        checks the length of the input groupings. Normally, a list of groups and list of data sources
        are input, such as...
        [source1, source2]
        [[group set 1], [group set 2]]
        with group set 1 = [1,2,3,4,5]
        Matching source 1 with group set 1, and source 2 with group set 2
        if there are a mismatch of group sets and sources, the dataframe is adjusted to fix that.
        '''
        if type(grouping) == list:
            if type(grouping[0]) != list:
                if len_DataSources > 1:
                    new_groups = []
                    for i in range(len_DataSources):
                        new_groups.append(grouping)
                    return new_groups
                else:
                    return [grouping]
            else:
                return grouping
        
    def _filter_by_StartDate(self, validIdx):
        '''
        takes a dataset and removes all data that 
        '''
        new_validIdx = []
        dateheader = self._checkforHeader('SampleDate')
        for idx in validIdx:
            curDate = dt.datetime.strptime(self.Data[dateheader].values[idx], '%m/%d/%Y %H:%M')
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
    
    def _get_Unique_Groups(self, DataFrame):
        '''
        Gets the number of unique groups in a dataset for legend plotting
        '''
        counted_Groups = []
        for index, row in DataFrame.iterrows():
            Group = row['Group']
            source = row['Source']
            GroupSource = (Group, source)
            if GroupSource not in counted_Groups:
                counted_Groups.append(GroupSource)
                
        return counted_Groups

    def _get_Correct_Pred_Sources(self, Group, GroupType, Pred_List):
        '''
        Grabs the list of predicted data and organzies them based on Cohort number for Total Cohort plots.
        Cohort 3 uses quantiles, 1, 2 and 3, Survey 5 uses 1,2,3,4,5, etc...
        HEAVILY depends on pred data named quantiles_x or tot_quantiles
        '''
        new_pred_list = []
        for Pred_source in Pred_List:
            if Pred_source.split('_')[0].lower() == 'tot':
                new_pred_list.append(Pred_source)
            else:
                try:
                    if float(Pred_source.split('_')[1]) <= Group:
                        new_pred_list.append(Pred_source)
                except:
                    print 'Unknown file name for predicted data:', Pred_source
                    checkadd = raw_input('Include {0} for {1} {2}? (Y/N)'.format(Pred_source, GroupType, Group)) 
                    while checkadd.lower() not in ['y', 'n']:
                        print 'Input {0} not understood. Please use Y or N to respond.'.format(checkadd)
                        checkadd = raw_input('Include {0} for {1} {2}? (Y/N)'.format(Pred_source, GroupType, Group)) 
                    if checkadd.lower() == 'y':
                        print 'Using {0} for {1} {2}'.format(Pred_source, GroupType, Group)
                        new_pred_list.append(Pred_source)
                    elif checkadd.lower() == 'n':
                        print 'Not using {0} for {1} {2}'.format(Pred_source, GroupType, Group)
                    else:
                        print 'You should never be here. Begone.'
                    
        return new_pred_list
    
    def _get_Group_Order(self, dataframe):
        '''
        Creates a new dataframe that identifies the start date for each Group and source, and then sorts
        that data based on the start date for chronological plots.
        '''
        
        Group_Order = pd.DataFrame(columns=['Group', 'Source', 'StartDate'])
        Groups = self._get_Unique_Groups(dataframe)
        for GroupSource in Groups:
            FiltData = dataframe.loc[dataframe['Group'] == GroupSource[0]]
            FiltData = FiltData.loc[FiltData['Source'] == GroupSource[1]]
            earliest_Date = min([r for r in FiltData['StartDate'].values])
            Group_Order = Group_Order.append({'Group': GroupSource[0], 
                                              'Source': GroupSource[1], 
                                              'StartDate': earliest_Date},
                                              ignore_index=True)
            
        Group_Order = Group_Order.sort_values(['StartDate'])
            
        return Group_Order
    
    
    def _add_PlotOrder(self, dataFrame):
        '''
        Adds a plotorder field to the main dataframe, then uses a separate array (generated from 
        self._get_Group_Order() to determine plot order for chronological plots
        '''
        self.mainDataFrame['PlotOrder'] = 1
        i = 1
        for index, row in dataFrame.iterrows():
            update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Group'] == row['Group'] and DFrow['Source'] == row['Source']]
            for idx in update_idx:
                self._update_mainDataFrame(idx, {'PlotOrder':i})
            i += 1
            
    def _add_Dates(self, dataFrame):
        '''
        adds a startdate and enddate field for the maindataframe. Then grabs the corresponding values
        and assigns the correct values.
        '''
        self.mainDataFrame['StartDate'] = ''
        self.mainDataFrame['EndDate'] = ''
        for index, row in dataFrame.iterrows():
            update_idx = [r for r, DFrow in self.mainDataFrame.iterrows() if DFrow['Survey'] == row['Survey'] and DFrow['Source'] == row['Source'] and DFrow['Region'] == row['Region']]
            for idx in update_idx:
                self._update_mainDataFrame(idx, {'StartDate':row['StartDate']})
                self._update_mainDataFrame(idx, {'EndDate':row['EndDate']})
                
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
#         Source_ID = {}
        apply_to_pred = ''
        for i, src in enumerate(self.mainDataFrame['Source'].values):
            if 'sls' in src.lower() and src not in self.Source_IDs.keys():
                self.Source_IDs[src] = 'SLS'
            elif '20mm' in src.lower() and src not in self.Source_IDs.keys():
                self.Source_IDs[src] = '20mm'
            elif src not in self.Source_IDs.keys():
                print 'No identifier for data source {0}'.format(os.path.basename(src))
                print 'IDs are used to connect Observed and Predicted data, display chronological data, and display legends. Examples are 20mm and SLS.'
                unknown_ID = raw_input('Please enter a 3-4 letter ID for new data source: ')
                apply_to_pred = raw_input('Apply this ID to all Predicted Data? (Y/N): ')
                while apply_to_pred.lower() not in ['y','n']:
                    print 'Invalid input. Please use Y or N.'
                    apply_to_pred = raw_input('Apply this ID to all Predicted Data? (Y/N): ')
                if apply_to_pred.lower() == 'y':
                    print 'Applying ID {0} to all predicted data...'.format(unknown_ID)
                    for src in self.mainDataFrame['Source'].values:
                        self.Source_IDs[src] = unknown_ID.lower()
                else:
                    self.Source_IDs[src] = unknown_ID.lower()
        
        for index,row in dataframe.iterrows():
            Source = row['Source'].lower()
            apply_to_obs = ''
            if 'sls' in Source.lower():
                try:
                    path = self.Source_IDs.keys()[self.Source_IDs.values().index('SLS')]
                    IDval = 'SLS'
                except ValueError:
                    print 'SLS not found in Observed Source IDs. Use one of the following establish ID\'s or rerun.'
                    print 'Established ID\'s: {0}'.format(list(dict.fromkeys(self.Source_IDs.values())))
                    IDval = raw_input('ID Value: ').lower()
                    while IDval.lower() not in list(dict.fromkeys(self.Source_IDs.values())):
                        print 'Input not in established ID\'s.'
                        print 'Please enter a source from {0} or restart the script'.format(list(dict.fromkeys(self.Source_IDs.values())))
                        IDval = raw_input('ID Value: ').lower()
                    apply_to_obs = raw_input('Apply this ID to all Observed Data? (Y/N): ')
                    while apply_to_pred.lower() not in ['y','n']:
                        print 'Invalid input. Please use Y or N.'
                        apply_to_obs = raw_input('Apply this ID to all Observed Data? (Y/N): ')
                    if apply_to_obs.lower() == 'y':
                        print 'Applying ID {0} to all Observed data...'
                        for index,row in dataframe.iterrows():
                            if dataframe.ix[index, 'Source'] not in self.Source_IDs.keys()[self.Source_IDs.values().index(IDval)]:
                                dataframe.ix[index, 'Source'] = self.Source_IDs.keys()[self.Source_IDs.values().index(IDval)]
                        return dataframe
                dataframe.ix[index, 'Source'] = self.Source_IDs.keys()[self.Source_IDs.values().index(IDval)] #Source_ID['sls']
                
            elif '20mm' in Source:
                try:
                    path = self.Source_IDs.keys()[self.Source_IDs.values().index('20mm')]
                    IDval = '20mm'
                except ValueError:
                    print 'SLS not found in Observed Source IDs. Use one of the following establish ID\'s or rerun.'
                    print 'Established ID\'s: {0}'.format(list(dict.fromkeys(self.Source_IDs.values())))
                    IDval = raw_input('ID Value: ').lower()
                    while IDval not in list(dict.fromkeys(self.Source_IDs.values())):
                        print 'Input not in established ID\'s.'
                        print 'Please enter a source from {0} or restart the script'.format(list(dict.fromkeys(self.Source_IDs.values())))
                        IDval = raw_input('ID Value: ').lower()
                    apply_to_obs = raw_input('Apply this ID to all Observed Data? (Y/N): ')
                    while apply_to_pred.lower() not in ['y','n']:
                        print 'Invalid input. Please use Y or N.'
                        apply_to_obs = raw_input('Apply this ID to all Observed Data? (Y/N): ')
                    if apply_to_obs.lower() == 'y':
                        print 'Applying ID {0} to all Observed data...'
                        for index,row in dataframe.iterrows():
                            if dataframe.ix[index, 'Source'] not in self.Source_IDs.keys()[self.Source_IDs.values().index(IDval)]:
                                dataframe.ix[index, 'Source'] = self.Source_IDs.keys()[self.Source_IDs.values().index(IDval)]
                        return dataframe
                dataframe.ix[index, 'Source'] = self.Source_IDs.keys()[self.Source_IDs.values().index(IDval)] #Source_ID['sls']
                
            elif src not in self.Source_IDs.keys():
                print 'No identifier for data source {0}'.format(os.path.basename(src))
                print 'IDs are used to connect Observed and Predicted data, display chronological data, and display legends. Examples are 20mm and SLS.'
                print 'Existing and suggested IDs include {0}'.format(list(dict.fromkeys(self.Source_IDs.values())))
                unknown_ID = raw_input('Please enter a 3-4 letter ID for new data source: ')
                apply_to_pred = raw_input('Apply this ID to all Observed Data? (Y/N): ')
                while apply_to_pred.lower() not in ['y','n']:
                    print 'Invalid input. Please use Y or N.'
                    apply_to_pred = raw_input('Apply this ID to all Observed Data? (Y/N): ')
                if apply_to_pred.lower() == 'y':
                    print 'Applying ID {0} to all Observed data...'
                    for index,row in dataframe.iterrows():
                        dataframe.ix[index, 'Source'] = self.Source_IDs.keys()[self.Source_IDs.values().index(unknown_ID)]
                    return dataframe
                else:
                    dataframe.ix[index, 'Source'] = self.Source_IDs.keys()[self.Source_IDs.values().index(unknown_ID)]
                
        return dataframe
   
    def _get_Survey_Dates(self, dataFrame, Survey):
        '''
        Gets dates for all fish for a specific survey, region agnostic. Allows user to get a range of dates
        that a survey may be in in the event that the data is incomplete.
        Used mostly to get correct data for Predicted data.
        '''
        Survey_dates = []
        for index, row in dataFrame.iterrows():
            if row['Survey'] == Survey:
                if row['StartDate'].year == self.Year and row['EndDate'].year == self.Year:
                    Survey_dates.append(row['StartDate'])
                    Survey_dates.append(row['EndDate'])
        
        try:            
            startDate = min(Survey_dates)
        except ValueError:
            startDate = dt.datetime(1900,1,1)
        try:
            endDate = max(Survey_dates)
        except:
            endDate = dt.datetime(2100,1,1)
        
        return startDate, endDate
    
    def _get_boxwhisker_Date_values(self, StartDate, EndDate, Predicted_Data, update_idx):
        '''
        Extracts quantile data from the mainDataFrame for specific dates
        '''
        q5 = []
        q25 = []
        q50 = []
        q75 = []
        q95 = []
        for idx in update_idx:
            if StartDate <= Predicted_Data['Date'][idx] <= EndDate:
                q5.append(Predicted_Data['q5'][idx])
                q25.append(Predicted_Data['q25'][idx])
                q50.append(Predicted_Data['q50'][idx])
                q75.append(Predicted_Data['q75'][idx])
                q95.append(Predicted_Data['q95'][idx])
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
            Chronological_DataFrame = pd.DataFrame(columns=['Region', 'Group', 'StartDate', 'Source'])
            #check surveys vs num of data sources
            for i, datasource in enumerate(Chronological_data):
                self._read_data(datasource)
                for region in self.regions:
                    for Group in self.Groups[i]:
                        startDate = self.get_StartDate(region, Group, self.GroupType)
                        Chronological_DataFrame = Chronological_DataFrame.append({'Region':region,
                                                                                  'Group':Group,
                                                                                  'StartDate':startDate,
                                                                                  'Source':datasource},
                                                                                  ignore_index=True)
            
            Group_order = self._get_Group_Order(Chronological_DataFrame)
            Group_order = self._connect_Sources(Group_order)

            self._add_PlotOrder(Group_order)
        else:
            Group_order = self._get_Group_Order(self.mainDataFrame)
            self._add_PlotOrder(Group_order)
            
    def add_Dataset(self, data, load_order, datatype=None):
        '''
        Reads in dataset and gets the main data, and then adds it to the master dataframe
        '''
        self._read_Data(data)
        
#         if datatype in ['multipredicted', 'cohort','hatch', 'entrainment','condensed_predicted']:
#             for region in self.regions:
#                 if self.plottype == 'boxwhisker':
#                     region_df = self._get_Region_Stats(region, 0, GroupType, datatype=datatype)
#                     region_df['Source'] = os.path.basename(data).split('.')[0]
#                     region_df['LoadOrder'] = load_order
#                     region_df['GroupType'] = GroupType
#                     self._merge_with_mainDataFrame(region_df)
#                 self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
                
#         elif datatype in ['observed', 'predicted']:
        if datatype in ['temp']:
            if self.plottype == 'boxwhisker':
                df = self._get_Stats(datatype=datatype)
                df['Source'] = os.path.basename(data).split('.')[0]
                df['LoadOrder'] = load_order
                self._merge_with_mainDataFrame(df)
            self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
            
            
        else:
            if self.plottype == 'boxwhisker':
                df = self._get_Stats(datatype=datatype)
                df['Source'] = os.path.basename(data).split('.')[0]
                if datatype == 'observed':
                    df['LoadOrder'] = 0
                else:
                    df['LoadOrder'] = load_order + 1
                self._merge_with_mainDataFrame(df)
            elif self.plottype == 'timeseries':
                df = self._get_Stats(datatype=datatype)
                df['Source'] = os.path.basename(data).split('.')[0]
                self._merge_with_mainDataFrame(df)
            self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
        
        
            

#         elif datatype == None:
#             for region in self.regions:
#                 for Group in Groups:
#                     if self.plottype == 'bar':
#                         abundance, density, firstDate = self._get_Region_Stats(region, Group, GroupType, Sizes=self.Sizes, datatype=datatype)
#                         density *= self._get_Density_Scalar(data)
#                         self._append_mainDataframe(Region=region, Group=Group, GroupType=GroupType, StartDate=firstDate, LoadOrder=load_order,
#                                                    Source=data, Abundance=abundance, Density=density)
#                     elif self.plottype == 'boxwhisker':
#                         q5, q25, q50, q75, q95 = self._get_Region_Stats(region, Group, GroupType, datatype=datatype)
#                         self._append_mainDataframe(Region=region, Group=Group, GroupType=GroupType, Source=data, LoadOrder=load_order,
#                                                    q5=q5, q25=q25, q50=q50, q75=q75, q95=q95)
#                     elif self.plottype == 'timeseries':
#                         ts_data = self._get_Region_Stats(region, Group, GroupType, datatype=datatype)
#                         self._append_mainDataframe(Region=region, Group=Group, GroupType=GroupType, Source=data, LoadOrder=load_order,
#                                                    Values=ts_data)

    def InitializeData(self, data, datatype=None, Label=None):
        '''
        Takes in a dataset and adds it to the main dataframe
        '''
        
        if type(data) == str:
            len_data = 1
            data = [data]
        elif type(data) == list:
            len_data = len(data)
        
#         if datatype in ['entrainment']:
#             self.Cohorts = self._check_groupingLength(len_data, self.Cohorts)
#         else:
#             self.Surveys = self._check_groupingLength(len_data, self.Surveys)
       
        if datatype in ['total_predicted', 'total_observed', 'predicted', 'observed', 'entrainment', 'hatch', 'timeseries']:
            for i, data_Source in enumerate(data):
                if self.plottype == 'boxwhisker':
                    self.add_Dataset(data_Source, i,  datatype=datatype)
                elif self.plottype == 'timeseries':
                    self.add_Dataset(data_Source, i,  datatype=datatype)
                elif self.plottype == 'bar':
                    print '{0} Dataset Bar plots not yet implemented.'.format(datatype)
                    print 'Now Exiting...'
                    sys.exit(0)
        
        elif datatype == None: 
            for i, data_Source in enumerate(data):
                self.add_Dataset(data_Source, i, self.Groups[i], self.GroupType)
#                     
        else:
            print 'unknown datatype. Now Exiting...'
            sys.exit(0)
         
            
        if Label == None:
            self._getLabels()
            self._setLabels()
        else:
            self._setLabels(Label=Label)
        
        print 'Added {0} Dataset(s)'.format(len(data))
                
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
                    current_Group = row['Group']
                    if source != row['Source']:
                        self._read_data(row['Source']) #make sure you reopen the correct file, else it will use the last file
                    source = row['Source']
                    abundance, density, firstDate = self._get_Region_Stats(region, current_Group, self.GroupType, Sizes=calculated_sizes[i])
                    density *= self._get_Density_Scalar(source)
                    self._update_mainDataFrame(index, {'Abundance': abundance, 'Density': density})
                    i += 1
    
    def get_Dates(self, Dataset, startdate=None, obsenddate=None):
        '''
        Creates a new dataframe that keeps track of the region, survey, starttime, endtime, and source.
        reads in the passed in dataframe, then gathers the correct data, and connects the data
        sources. Then adds dates to main dataframe.
        '''
        DataFrame = pd.DataFrame(columns=['Region', 'Survey', 'StartDate', 'EndDate', 'Source'])
        
        if type(Dataset) == str:
            Dataset = [Dataset]
#         elif type(Dataset) == list:

        for i, datasource in enumerate(Dataset):
            self._read_Data(datasource)
            for region in self.regions:
                    for Survey in self.Surveys[i]:
                        if startdate != None:
                            startDate = dt.datetime.strptime(startdate, '%Y-%m-%d')
                        else:
                            startDate = self.get_StartDate(region, Survey)
                        if obsenddate != None:
                            endDate = dt.datetime.strptime(startdate, '%Y-%m-%d') + dt.timedelta(days=1)
                        else:
                            endDate = self.get_EndDate(region, Survey)
                        DataFrame = DataFrame.append({'Region':region,
                                                      'Survey':Survey,
                                                      'StartDate':startDate,
                                                      'EndDate':endDate,
                                                      'Source':datasource},
                                                      ignore_index=True)
        DataFrame = self._connect_Sources(DataFrame)
        self._add_Dates(DataFrame)
            
    def Coordinate_Data(self, Predicted_Data, Observed_Data, datatype=None, Survey=None):   
        '''
        Gets the correct predicted time series data from Computed data excel files. 
        Observed forms give daily values for q5, q25, q50, q75, and q95 regional values.
        By using an observed data file, dates for each region and survey are grabbed.
        Values from the computed file are then averaged over the selected days and returned in a dataframe.
        
        If Total flag is true, Values for each survey are computed by iterating through each 
        observed file. A date for each survey is found. Then each quantiles file before the
        '''  
#         Avg_Pred_Df = pd.DataFrame(columns=['Region', 'Survey', 'Source', 'q5', 'q25', 'q50', 'q75', 'q95'])
        Valid = []
        Predicted_Data['Survey'] = ''
        for obs_index, row in Observed_Data.iterrows():
            valid_idx = [r for r, DFrow in Predicted_Data.iterrows() if DFrow['Date'] == row['Date'] 
                         and DFrow['Region'] == row['Region']]
            Valid += valid_idx
            for i in valid_idx:
                Predicted_Data.ix[i,'Survey'] = row['Survey']
        Valid = list(dict.fromkeys(Valid))
        Predicted_Data = Predicted_Data.loc[Valid]
        dataframe = self.merge_Dataframes(Predicted_Data, Observed_Data)        
        return dataframe
    
    def get_StartDate(self, Region, Survey):
        '''
        Finds and returns the earliest start date for specific region and group.
        returns a datetime object
        '''
        Earliest_Group_Date = dt.datetime(2100,1,1)
        
        dateheader = self._checkforHeader('SampleDate')
        
        region_idx = self._get_Valid_Idx(Region, 'lfs_region')
        Survey_Idx = self._get_Valid_Idx(Survey, 'Survey', Filter=region_idx)
        valid_idx = self._get_Valid_Idx(self.Year, 'Year', Filter=Survey_Idx)
        
        for index in valid_idx:
            current_date = dt.datetime.strptime(self.Data[dateheader].values[index], '%m/%d/%Y %H:%M')
            if current_date < Earliest_Group_Date:
                Earliest_Group_Date = current_date
                    
        return Earliest_Group_Date
    
    def get_EndDate(self, Region, Survey):
        '''
        Finds and returns the latest end date for specific region and group.
        returns a datetime object
        '''
        Latest_Group_Date = dt.datetime(1900,1,1)
        
        dateheader = self._checkforHeader('SampleDate')
        
        region_idx = self._get_Valid_Idx(Region, 'lfs_region')
        Survey_Idx = self._get_Valid_Idx(Survey, 'Survey', Filter=region_idx)
        valid_idx = self._get_Valid_Idx(self.Year, 'Year', Filter=Survey_Idx)
        
        for index in valid_idx:
            current_date = dt.datetime.strptime(self.Data[dateheader].values[index], '%m/%d/%Y %H:%M')
            if current_date > Latest_Group_Date:
                Latest_Group_Date = current_date
                    
        return Latest_Group_Date

    def get_DataFrame(self, cohort=None):
        '''
        returns the current dataframe object
        '''
        if cohort == None:
            return self.mainDataFrame
        elif cohort != None:
            valid_idx = np.where(self.mainDataFrame['Cohort'] == cohort)
       
            
        return self.mainDataFrame.loc[valid_idx]
        
    def get_Cohorts(self, cohorts):
        if type(cohorts) == list:
            available_cohorts = self.mainDataFrame.Cohort.unique()
            approved_cohorts = []
            for item in cohorts:
                if item not in available_cohorts:
                    print 'Cohort {0} not available in Predicted Data. Removing Cohort {0}.'.format(item) 
                else:
                    print item
                    approved_cohorts.append(item)
            return approved_cohorts
        elif cohorts.lower() == 'all':
            return self.mainDataFrame.Cohort.unique()
        else:
            print 'Unrecognized cohorts set: {0}'.format(cohorts)
            print 'Please confirm cohorts and rerun. Now exiting...'
            sys.exit(0)
            
    def correct_Groups(self, Groups):
        '''
        removes unused surveys from the mainDataframe. Currently unusued.
        '''
        self.Group=[Groups]
        for index, row in self.mainDataFrame.iterrows():
            if row['Group'] not in self.Groups[0]:
                self.mainDataFrame = self.mainDataFrame.drop([index])
                
        self.mainDataFrame = self.mainDataFrame.reset_index(drop=True)
    
    def merge_Dataframes(self, dataset1, dataset2):
        '''
        Merges two similar dataframes together and resets the index.
        Columns not shared will be added
        '''
        new_dataframe = pd.concat([dataset1, dataset2]).reset_index(drop=True)
        
        return new_dataframe
    
    def Filter_by_Surveys(self, dataframe, Surveys):
        for i, row in dataframe.iterrows():
            if row['Survey'] not in Surveys:
                dataframe.drop(i, inplace=True)
        return dataframe
    
    def Filter_by_HatchDate(self, dataframe, hatching_period=None):
        hatchdate = dataframe.Hatchstart.unique()
        if len(hatchdate) > 1:
            print 'Number of hatchdates for Cohort {0} exceeds 1.'
            print 'Please check data and try again.'
            sys.exit(0)
        for i, row in dataframe.iterrows():
            if hatching_period is None:
                end_hatching = hatchdate[0]
            else:
                dt_hatch = np.timedelta64(hatching_period,'D')
                end_hatching = hatchdate[0] + dt_hatch
            #if row['Date'] < hatchdate[0]:
            if row['Date'] < end_hatching:
                dataframe.drop(i, inplace=True)
        return dataframe
    
    def Organize_Data(self, dataframe, datatype):
        if datatype in ['entrainment']:
            last_cohort_date = {}
            cohorts = dataframe.Cohort.unique()
            for cohort in cohorts:
                latest_date = dt.datetime(1900,1,1)
                dates = [row['Date'] for r, row in dataframe.iterrows() if row['Cohort'] == cohort]
                for date in dates:
                    if date > latest_date:
                        latest_date = date
                last_cohort_date[cohort] = latest_date
            Valid = []
            for cohort in last_cohort_date.keys():
                valid_idx = [r for r, DFrow in dataframe.iterrows() if DFrow['Cohort'] == cohort 
                             and DFrow['Date'] == last_cohort_date[cohort]]

                Valid += valid_idx
            Valid = list(dict.fromkeys(Valid))
            return dataframe.loc[Valid]
        
        else:
            return dataframe
        
