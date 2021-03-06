# Use for plotting SLS and 20mm survey data

import os, sys
import csv
import numpy as np
from scipy import stats
import pandas as pd
import pylab
import matplotlib.pyplot as plt
import pdb
from datetime import datetime as dt
import math
from stompy.grid import unstructured_grid
from rmapy.utils.gis import polygons_w_attributes_from_shp as polys_from_shp
import Longfin_Plot_Utils


# to do
# - generalize to incorporate data from multiple surveys
# - add "ocean" region to ptm
# - add "landward" region to ptm


class LongfinMaps(object):

    def __init__(self,
                 run_dir,
                 grd_file,
                 year):
        self.run_dir = run_dir
        self.grd_file = grd_file
        self.year = year
        self.get_inputs()

    def get_inputs(self):
        # inputs used across all CAMT cases
        self.xylims = [530000,661500,4138000,4295000]
        shp = r"C:\git\longfin_trawl_map\Longfin_hatching_regions.shp"
        dict_field_name = 'Region'
        inpfile = 'FISH_PTM.inp'
        
        skip_regions=[]
        
        self.FRAC_FLAG = True
        
        self.inpfile = os.path.join(self.run_dir,inpfile)

        # Read .shp file
        atts,pdict = polys_from_shp.PolysWAtts(shp,poly_dict=True, dict_field_name=dict_field_name)
        self.poly_names = atts[dict_field_name]
        self.pdict = pdict

        self.plot_poly_dict = {}
        for npoly,pname in enumerate(self.poly_names):
            pname_=pname.replace(" ","_")
            if pname_ not in skip_regions:            
                self.plot_poly_dict[pname_] = self.pdict[pname_]
          
        # use FISH-PTM grid for background with both models
        self.grd = unstructured_grid.PtmGrid(self.grd_file)
        
        self.utm_dict = {'Central_Delta_and_Franks_Tract':[618495.3074911481,4212214.95338295],
            'Upper_Sacramento_River':[629749.8528383253,4244678.154020051],
            'North_and_South_Forks_Mokelumne_River':[640841.2233035656,4219130.996234625],
            'South_Delta':[642592.4377057501,4189918.7990992256],
            'Cache_Slough_Complex':[615123.5756282026,4262158.33897849],
            'Confluence':[606111.7244591176,4214227.897524303],
            'Suisun_Bay':[587330.4530226303,4207893.7344756285],
            'Carquinez_Strait':[571227.4604096551,4209182.676400363], 
            'Suisun_Marsh':[585992.6837656068,4231349.288782105],
            'San_Pablo_Bay':[553942.9282736651,4208647.568697553],
            'Petaluma':[540030.1280006216,4221490.153564978],
            'South_SF_Bay':[566963.8823753597,4165482.214004264],
            'Central_SF_Bay':[549337.8061231661,4188897.4110258943], 
            'Lower_South_SF_Bay':[586049.3904422284,4145683.2290003207], 
            'Napa_Sonoma':[555580.7293226086,4232151.950336318]}

        self.max_ab = {2012:20000000,
                  2013:50000000,
                  2016:2500000,
                  2017:20000000}
        
        self.max_den = {2012:750,
                   2013:7500,
                   2016:500,
                   2017:750}


        return
    
### ~~~~~~~~~~~~~~~~ DATA WRANGLING ~~~~~~~~~~~~~~~~ ###
    def check_runtype(self):
        #checks the run type to set up the correct density modifier. When data is converted from Abundance to Density, SLS and 20mm use different scales.
        #ie fish per 1000 cubic meters, 100000 cubic meters, etc...
        accepted_runtypes = {'sls':1000., 
                             '20mm':10000.}
        while self.runtype.lower() not in accepted_runtypes.keys():
            self.runtype = raw_input('Run type of {0} not support. Please enter a supported run type listed here: {1}'.format(self.runtype, ', '.join(accepted_runtypes.keys())))
        self.runtype = self.runtype.lower()
        self.density_units = accepted_runtypes[self.runtype]
        
    def check_multisurveys(self):
        '''
        Check to make sure Multi surveys are set up correctly where needed
        It is not immediatly apparent these are needed, so best just to be sure they are set up correctly, especially if the funtion is iterated by another script
        '''
        try: self.multisurveys
        except AttributeError: 
            print 'Multisurveys not defined. Please define survey numbers for each data source before Multicohort function is called.'
            print 'Even if both data sources use the same survey numbers, make sure there is data for each.'
            print 'The data structure is as follows: [[2,3,4,5],[2,3,4,5]]'
            print 'Example of defining the variables:'
            print 'cbm = LongfinMaps(run_dir, grd_file, year) #call the class, named cbm'
            print 'cbm.multisurveys = [[3,4,5,6], [2,3,4,5,6,7]] #define the surveys for the class'
            print 'cbm.make_MultiCohort_Plot(obs_data1, obs_data2, figname, size_range, static_volumes) #then call the multicohort plot function.'
            print 'Script is now exiting...'
            sys.exit(0)
            
    def filter_by_startDate(self, in_idx, start_Date):

        for i, idx in enumerate(in_idx):
            try:
                surv_Date = dt.strptime(self.obs_df['SampleDate'].values[idx], '%m/%d/%Y %H:%M')
            except ValueError:
                surv_Date = dt.strptime(self.obs_df['SampleDate'].values[idx], '%Y-%m-%d %H:%M:%S')
            if surv_Date < start_Date:
                print 'deleted {0} at {1}'.format(idx, self.obs_df['SampleDate'].values[idx])
                del in_idx[i]
        return in_idx
    
    def findNoData(self, Surveys, obs_data):
        '''
        Finds area in data files that have no data and creates a labels array for plotting
        areas with no data are assigned an 'X' to show a non zero no data value
        Requires the datatype to be set, as different data gets called different ways
        '''
        regions = self.poly_names
        labels = np.chararray((len(regions), len(Surveys)))
        labels[:] = 'X'
        
        
        if self.datatype == 'Precalculated':
            valid_idx = [r for r, survey in enumerate(obs_data['survey'].values) if survey in Surveys]
            for idx in valid_idx:
                if not np.isnan(obs_data['q5'].values[idx]):
                    cur_region = obs_data['region'][idx].replace(' ', '_')
                    reg_idx = regions.index(cur_region)
                    cur_surv = obs_data['survey'][idx]
                    surv_idx = Surveys.index(cur_surv)
                    labels[reg_idx][surv_idx] = ''
                    
        elif self.datatype == 'Observed':
            valid_idx = [r for r, date in enumerate(obs_data['Year'].values) if date == self.year and obs_data['Survey'][r] in Surveys]
            for idx in valid_idx:
                cur_region = obs_data['lfs_region'][idx]
                reg_idx = regions.index(cur_region)
                cur_surv = obs_data['Survey'][idx]
                bar_idx = Surveys.index(cur_surv)
                labels[reg_idx][bar_idx] = ''
        
        
        else:
            print 'Undefined type for getting missing data labels.'
            print 'Entered type: {0}. Continuing with no labels.'.format(self.datatype)
            labels[:] = ''
 
        return labels
    
    def get_Obs_data(self, year, Surveys, size_range):
        '''
        Reads Long file and converts counts per survey into density and Reg Abundance.
        Splits data up into Region - Year - Survey
        Writes output text file for quick check of data numbers
        '''
        valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['Survey'][r] in Surveys]

        obs_count = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        obs_vol = np.zeros((len(self.poly_names), len(Surveys)),np.float64)
        obs_density = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        reg_abundance = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        
        for i in valid_idx:
            cur_region = self.obs_df['lfs_region'].values[i]
            cur_survey = self.obs_df['Survey'].values[i]
            cur_vol = self.obs_df['Volume'].values[i]
            poly_idx = self.poly_names.index(cur_region)
            bar_idx = Surveys.index(cur_survey)

            if isinstance(size_range, str):
                fish_counts = self.countAllFishSizes(i, self.obs_df)
            else:
                fish_counts = self.countSomeFishSizes(i, size_range, self.obs_df)
            obs_count[poly_idx][bar_idx] += fish_counts
            obs_vol[poly_idx][bar_idx] += cur_vol
            
        with open('Obs_data_output_{0}_{1}mm-{2}mm.csv'.format(year, size_range[0], size_range[1]), 'wb') as outtext:    
            outtext.write('region,year,survey,fish count,volume per Survey,Density in {0} fish per m3,Region Volume,Reg Abundance\n'.format(self.density_units))
            for i, region in enumerate(self.poly_names):
#                 print region
                vol_file_idx = np.where(self.obs_static_vol['region_name'].values == region.replace('_',' '))[0][0]
                region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
                for j, survey_cnt in enumerate(obs_count[i]):
#                     print survey_cnt
                    obs_density[i][j] = survey_cnt / obs_vol[i][j] 
                    reg_abundance[i][j] = obs_density[i][j] * region_vol
                    reg_abundance = np.nan_to_num(reg_abundance)
                    outline = ','.join([str(r) for r in [region, year, j+1, survey_cnt, obs_vol[i][j], obs_density[i][j] * self.density_units, region_vol, reg_abundance[i][j], '\n']])
                    outtext.write(outline)
        
        return reg_abundance
    
    def get_Cohort_Data(self, year, Surveys, size_range):
        '''
        structure = [Region1[[surv1, sizes, dates], [surv2, sizes, dates]], Region2[[surv1, sizes, dates], [surv2, sizes, dates]]]
        example: The amount of grown in 14 days is 14 days*0.14 mm/day = 1.96 mm
        
        '''
        #set growth rate for multiple functions. Has changed from .14 to .2 at times
        Growth_Rate = self.growth_rate
#         valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['Survey'][r] in Surveys]
        
        coh_count = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        coh_vol = np.zeros((len(self.poly_names), len(Surveys)),np.float64)
        coh_density = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        coh_abundance = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        coh_dates = np.zeros((len(self.poly_names),len(Surveys)),dtype=object)
        coh_sizes = np.zeros((len(self.poly_names),len(Surveys)),dtype=object)
        
        orig_size_range = size_range[:] #keep the original size range to be reset between regions
        #deal with dates and sizes first
        #For each region and survey, get the dates between each survey and use to create a size range for each 
        for reg_idx, region in enumerate(self.poly_names):
            in_reg_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['lfs_region'][r] == region and self.obs_df['Survey'][r] in Surveys]
            size_range = orig_size_range[:] #reset for each region...
            for surv_idx, surv in enumerate(Surveys): #go through prescribed surveys
                in_surv_idx = [r for r in in_reg_idx if self.obs_df['Survey'][r] == surv] #get each index in prev list where survey is current survey
                for idx in in_surv_idx:
                    try:
                        cur_date = dt.strptime(self.obs_df['SampleDate'][idx], '%m/%d/%Y 0:00') #SLS format
                    except ValueError:
                        cur_date = dt.strptime(self.obs_df['SampleDate'][idx], '%Y-%m-%d 00:00:00') #20mm format
                    if isinstance(coh_dates[reg_idx][surv_idx], int): #check for NAN dates
                        coh_dates[reg_idx][surv_idx] = [cur_date]
                    else:
                        coh_dates[reg_idx][surv_idx] = np.append(coh_dates[reg_idx][surv_idx], cur_date)
                
                if len(in_surv_idx) > 0:
                    coh_dates[reg_idx][surv_idx] = (min(coh_dates[reg_idx][surv_idx]), max(coh_dates[reg_idx][surv_idx]))
                    if surv_idx == 0:
                        coh_sizes[reg_idx][surv_idx] = size_range[:]
                    else:
                        last_date = coh_dates[reg_idx][surv_idx -1][1]
                        if not isinstance(last_date, float):
                            time_elapsed = coh_dates[reg_idx][surv_idx][0] - last_date
                            growth = time_elapsed.days * Growth_Rate
                            growth_round = int(math.ceil(growth))
                            size_range[0] += growth_round
                            size_range[1] += growth_round
                            coh_sizes[reg_idx][surv_idx] = size_range[:]
                        else:
                            coh_sizes[reg_idx][surv_idx] = size_range[:]
                else:
                    coh_sizes[reg_idx][surv_idx] = size_range[:]
                    coh_dates[reg_idx][surv_idx] = (np.nan, np.nan)

        
    
        for reg_idx, region in enumerate(self.poly_names): #go by each region
            #find index where the year, region, and listed surveys
            in_reg_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['lfs_region'][r] == region and self.obs_df['Survey'][r] in Surveys]
            for surv_idx, surv in enumerate(Surveys): #go through prescribed surveys
                in_surv_idx = [r for r in in_reg_idx if self.obs_df['Survey'][r] == surv] #get each index in prev list where survey is current survey
                for idx in in_surv_idx:
                    cur_vol = self.obs_df['Volume'].values[idx]
                    if isinstance(coh_sizes[reg_idx][surv_idx], str):
                        fish_counts = self.countAllFishSizes(idx, self.obs_df)
                    else:
                        fish_counts = self.countSomeFishSizes(idx, coh_sizes[reg_idx][surv_idx], self.obs_df)    
                         
                    coh_count[reg_idx][surv_idx] += fish_counts
                    coh_vol[reg_idx][surv_idx] += cur_vol   
                     
        with open('Cohort_data_output_{0}.csv'.format(year), 'wb') as outtext:    
            outtext.write('region,survey,Date_Start,Date_End,year,size min,size max,fish count,volume per Survey,Density in {0} fish per m3,Region Volume,Reg Abundance\n'.format(self.density_units))
            for reg_idx, region in enumerate(self.poly_names):
                vol_file_idx = np.where(self.obs_static_vol['region_name'].values == region.replace('_',' '))[0][0]
                region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
                for surv_idx, surv_count in enumerate(coh_count[reg_idx]):
                    coh_density[reg_idx][surv_idx] = surv_count / coh_vol[reg_idx][surv_idx] 
                    coh_abundance[reg_idx][surv_idx] = coh_density[reg_idx][surv_idx] * region_vol
                    coh_abundance = np.nan_to_num(coh_abundance)
                    try:
                        outline = ','.join([str(r) for r in [region, surv_idx+1,coh_dates[reg_idx][surv_idx][0].strftime('%m/%d'),coh_dates[reg_idx][surv_idx][1].strftime('%m/%d'), year, coh_sizes[reg_idx][surv_idx][0], coh_sizes[reg_idx][surv_idx][1], surv_count, coh_vol[reg_idx][surv_idx], coh_density[reg_idx][surv_idx] * self.density_units, region_vol, coh_abundance[reg_idx][surv_idx], '\n']])
                    except AttributeError:
                        outline = ','.join([str(r) for r in [region, surv_idx+1,'nan','nan', year, coh_sizes[reg_idx][surv_idx][0],coh_sizes[reg_idx][surv_idx][1], surv_count, coh_vol[reg_idx][surv_idx], coh_density[reg_idx][surv_idx] * self.density_units, region_vol, coh_abundance[reg_idx][surv_idx], '\n']])
                    outtext.write(outline)

        return coh_abundance
    
    
    def get_dates_and_sizes(self, obs_file, year, Surveys, size_range, growthRate):
        
        coh_dates = np.zeros((len(self.poly_names),len(Surveys)),dtype=object)
        coh_sizes = np.zeros((len(self.poly_names),len(Surveys)),dtype=object)
        
        orig_size_range = size_range[:]
        #deal with dates and sizes first
        for reg_idx, region in enumerate(self.poly_names):
            in_reg_idx = [r for r, date in enumerate(obs_file['Year'].values) if date == year and obs_file['lfs_region'][r] == region and obs_file['Survey'][r] in Surveys]
            size_range = orig_size_range[:]
            for surv_idx, surv in enumerate(Surveys): #go through prescribed surveys
                in_surv_idx = [r for r in in_reg_idx if obs_file['Survey'][r] == surv] #get each index in prev list where survey is current survey
                for idx in in_surv_idx:
                    try:
                        cur_date = dt.strptime(obs_file['SampleDate'][idx], '%m/%d/%Y 0:00') #SLS format
                    except ValueError:
                        cur_date = dt.strptime(obs_file['SampleDate'][idx], '%Y-%m-%d 00:00:00') #20mm format
                    if isinstance(coh_dates[reg_idx][surv_idx], int):
                        coh_dates[reg_idx][surv_idx] = [cur_date]
                    else:
                        coh_dates[reg_idx][surv_idx] = np.append(coh_dates[reg_idx][surv_idx], cur_date)
                
                if len(in_surv_idx) > 0:
                    
                    coh_dates[reg_idx][surv_idx] = (min(coh_dates[reg_idx][surv_idx]), max(coh_dates[reg_idx][surv_idx]))
                    if surv_idx == 0:
                        coh_sizes[reg_idx][surv_idx] = size_range[:]
                    else:
                        last_date = coh_dates[reg_idx][surv_idx -1][1]
                        if not isinstance(last_date, float):
                            time_elapsed = coh_dates[reg_idx][surv_idx][0] - last_date
                            growth = time_elapsed.days * growthRate
                            growth_round = int(math.ceil(growth))
                            size_range[0] += growth_round
                            size_range[1] += growth_round
                            coh_sizes[reg_idx][surv_idx] = size_range[:]
                        else:
                            coh_sizes[reg_idx][surv_idx] = size_range[:]
                else:
                    coh_sizes[reg_idx][surv_idx] = size_range[:]
                    coh_dates[reg_idx][surv_idx] = (np.nan, np.nan)
                
        return coh_dates, coh_sizes
    
    def get_chron_dates_and_sizes(self, run_DF, year, size_range, growthRate):

        
        coh_dates = np.zeros((len(self.poly_names),len(run_DF[2])),dtype=object)
        coh_sizes = np.zeros((len(self.poly_names),len(run_DF[2])),dtype=object)
        
        orig_size_range = size_range[:]
        #deal with dates and sizes first
        for reg_idx, region in enumerate(self.poly_names):
            size_range = orig_size_range[:]
            for surv_idx, surv in enumerate(run_DF[2]):
                if run_DF[1][surv_idx] == 0:
                    obs_file = self.obs_df1
                else:
                    obs_file = self.obs_df2
                print ''
                print 'file_num =', run_DF[1][surv_idx]
                print 'surv_idx =', surv_idx
                print 'reg_idx =', reg_idx
                print 'dates =', run_DF[0][surv_idx]

                in_idx = [r for r, date in enumerate(obs_file['Year'].values) if date == year and obs_file['lfs_region'][r] == region and obs_file['Survey'][r] == surv]
#                 size_range = orig_size_range[:]
#                 for surv_idx, surv in enumerate(Surveys): #go through prescribed surveys
#                     in_surv_idx = [r for r in in_reg_idx if obs_file['Survey'][r] == surv] #get each index in prev list where survey is current survey
                for idx in in_idx:
                    try:
                        cur_date = dt.strptime(obs_file['SampleDate'][idx], '%m/%d/%Y 0:00') #SLS format
                    except ValueError:
                        cur_date = dt.strptime(obs_file['SampleDate'][idx], '%Y-%m-%d 00:00:00') #20mm format
                    print cur_date, region, surv
                    if isinstance(coh_dates[reg_idx][surv_idx], int):
                        coh_dates[reg_idx][surv_idx] = [cur_date]
                    else:
                        coh_dates[reg_idx][surv_idx] = np.append(coh_dates[reg_idx][surv_idx], cur_date)
                
                if len(in_idx) > 0:
                    
                    coh_dates[reg_idx][surv_idx] = (min(coh_dates[reg_idx][surv_idx]), max(coh_dates[reg_idx][surv_idx]))
                    if surv_idx == 0:
                        coh_sizes[reg_idx][surv_idx] = size_range[:]
                        print size_range
                    else:
                        last_date = coh_dates[reg_idx][surv_idx -1][1]
                        if not isinstance(last_date, float):
                            time_elapsed = coh_dates[reg_idx][surv_idx][0] - last_date
                            growth = time_elapsed.days * growthRate
                            growth_round = int(math.ceil(growth))
                            size_range[0] += growth_round
                            size_range[1] += growth_round
                            coh_sizes[reg_idx][surv_idx] = size_range[:]
                        else:
                            coh_sizes[reg_idx][surv_idx] = size_range[:]
                        print size_range
                else:
                    coh_sizes[reg_idx][surv_idx] = size_range[:]
                    coh_dates[reg_idx][surv_idx] = (np.nan, np.nan)
                
        return coh_dates, coh_sizes
        
        
    def get_Cohort_start_dates(self, year, Surveys, size_range):    
        total_surv = 0
        all_surveys = []
        for section in Surveys:
            total_surv += len(section)
            for surv in section:
                all_surveys.append(surv)
                
        file_sources = [self.obs_df1, self.obs_df2]
        growth_Rate = self.growth_rate
        for obs_idx, obs_file in enumerate(file_sources):
            dates, sizes = self.get_dates_and_sizes(obs_file, year, Surveys[obs_idx], size_range)
            if obs_idx == 0:
                coh_dates = dates
                coh_sizes = sizes
            else:
                coh_dates = np.column_stack((coh_dates, dates))
                coh_sizes = np.column_stack((coh_sizes, sizes))       
                
        return coh_dates
    
    def get_Chronological_Multicohort_Data(self, year, Surveys, size_range, start_Date=None):  
        '''
        Organizes surveys into chronological order, then gets and organizes the BW data accordingly. 
        By passing in a start date, the user can filter dates prior to date
        '''
        
        all_surv_Dates = []
        surv_date_info = np.zeros((2, 2), dtype=object)
        surv_date_info[0][1] = self.obs_df1
        surv_date_info[1][1] = self.obs_df2
        for surv_set_idx, surv_set in enumerate(Surveys):
            surv_date_info[surv_set_idx][0] = np.zeros(len(surv_set), dtype=object)
            for surv_idx, surv in enumerate(surv_set):
                date_idxs = [r for r, date in enumerate(surv_date_info[surv_set_idx][1]['Year'].values) if date == year and surv_date_info[surv_set_idx][1]['Survey'][r] == surv]
                tmp_Dates = []
                for r in date_idxs:
                    try:
                        tmp_Dates.append(dt.strptime(surv_date_info[surv_set_idx][1]['SampleDate'].values[r], '%m/%d/%Y %H:%M'))
                    except:
                        tmp_Dates.append(dt.strptime(surv_date_info[surv_set_idx][1]['SampleDate'].values[r], '%Y-%m-%d %H:%M:%S'))
                        
                surv_date_info[surv_set_idx][0][surv_idx] = tmp_Dates
                all_surv_Dates.append([tmp_Dates, surv_set_idx, surv])

        run_DF = pd.DataFrame(all_surv_Dates).sort_values(by=[0]).reset_index(drop=True)
        
        Growth_rate = self.growth_rate
        coh_count = np.zeros((len(self.poly_names),len(run_DF[1])),np.float64)
        coh_vol = np.zeros((len(self.poly_names), len(run_DF[1])),np.float64)
        coh_density = np.zeros((len(self.poly_names),len(run_DF[1])),np.float64)
        coh_abundance = np.zeros((len(self.poly_names),len(run_DF[1])),np.float64)
        

#             dates, sizes = self.get_dates_and_sizes(datafile, year, Surveys, size_range)
        coh_dates, coh_sizes = self.get_chron_dates_and_sizes(run_DF, year, size_range, Growth_rate)
#             
        for reg_idx, region in enumerate(self.poly_names): #go by each region
            #find index where the year, region, and listed surveys
            for surv_idx, surv in enumerate(run_DF[2]):
                if run_DF[1][surv_idx] == 0:
                    obs_data = self.obs_df1
                else:
                    obs_data = self.obs_df2
            
                in_idx = [r for r, date in enumerate(obs_data['Year'].values) if date == year and obs_data['lfs_region'][r] == region and obs_data['Survey'][r] == surv]
                if start_Date != None:
                    in_idx = self.filter_by_startDate(in_idx, start_Date)
                for idx in in_idx:
                    cur_vol = obs_data['Volume'].values[idx]
                    if isinstance(coh_sizes[reg_idx][surv_idx], str):
                        fish_counts = self.countAllFishSizes(idx, obs_data)
                    else:
                        fish_counts = self.countSomeFishSizes(idx, coh_sizes[reg_idx][surv_idx], obs_data)    
                         
                    coh_count[reg_idx][surv_idx] += fish_counts
                    coh_vol[reg_idx][surv_idx] += cur_vol   
                     
        with open('Cohort_Chron_data_output_{0}.csv'.format(year), 'wb') as outtext:    
            outtext.write('region,survey,Date_Start,Date_End,year,size min,size max,fish count,volume per Survey,Density in {0} fish per m3,Region Volume,Reg Abundance\n'.format(self.density_units))
            for reg_idx, region in enumerate(self.poly_names):
                vol_file_idx = np.where(self.obs_static_vol['region_name'].values == region.replace('_',' '))[0][0]
                region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
                for surv_idx, surv_count in enumerate(coh_count[reg_idx]):
                    coh_density[reg_idx][surv_idx] = surv_count / coh_vol[reg_idx][surv_idx] 
                    coh_abundance[reg_idx][surv_idx] = coh_density[reg_idx][surv_idx] * region_vol
                    coh_abundance = np.nan_to_num(coh_abundance)
                    try:
                        outline = ','.join([str(r) for r in [region, surv_idx+1,coh_dates[reg_idx][surv_idx][0].strftime('%m/%d'),coh_dates[reg_idx][surv_idx][1].strftime('%m/%d'), year, coh_sizes[reg_idx][surv_idx][0], coh_sizes[reg_idx][surv_idx][1], surv_count, coh_vol[reg_idx][surv_idx], coh_density[reg_idx][surv_idx] * self.density_units, region_vol, coh_abundance[reg_idx][surv_idx], '\n']])
                    except AttributeError:
                        outline = ','.join([str(r) for r in [region, surv_idx+1,'nan','nan', year, coh_sizes[reg_idx][surv_idx][0],coh_sizes[reg_idx][surv_idx][1], surv_count, coh_vol[reg_idx][surv_idx], coh_density[reg_idx][surv_idx] * self.density_units, region_vol, coh_abundance[reg_idx][surv_idx], '\n']])
                    outtext.write(outline)

        return run_DF, coh_abundance
    
    def get_Chronological_Multicohort_Boxwhisker_Data(self, year, Surveys, quantiles_file1, quantiles_file2):  
        '''
        Organizes surveys into chronological order, then gets and organizes the BW data accordingly. 
        '''
        
        all_surv_Dates = []
        surv_date_info = np.zeros((2, 2), dtype=object)
        surv_date_info[0][1] = self.obs_df1
        surv_date_info[1][1] = self.obs_df2
        for surv_set_idx, surv_set in enumerate(Surveys):
            surv_date_info[surv_set_idx][0] = np.zeros(len(surv_set), dtype=object)
            for surv_idx, surv in enumerate(surv_set):
                date_idxs = [r for r, date in enumerate(surv_date_info[surv_set_idx][1]['Year'].values) if date == year and surv_date_info[surv_set_idx][1]['Survey'][r] == surv]
                tmp_Dates = []
                for r in date_idxs:
                    try:
                        tmp_Dates.append(dt.strptime(surv_date_info[surv_set_idx][1]['SampleDate'].values[r], '%m/%d/%Y %H:%M'))
                    except:
                        tmp_Dates.append(dt.strptime(surv_date_info[surv_set_idx][1]['SampleDate'].values[r], '%Y-%m-%d %H:%M:%S'))
                        
                surv_date_info[surv_set_idx][0][surv_idx] = tmp_Dates
                all_surv_Dates.append([tmp_Dates, surv_set_idx, surv])

        run_DF = pd.DataFrame(all_surv_Dates).sort_values(by=[0]).reset_index(drop=True)

#         coh_dates, coh_sizes = self.get_chron_dates_and_sizes(run_DF, year, size_range, Growth_rate)
#         coh_vals = np.zeros((len(self.poly_names), len(run_DF[1])),dtype=object)
        for surv_idx, surv in enumerate(run_DF[2]):
            if run_DF[1][surv_idx] == 0:
                quant_data = quantiles_file1
            else:
                quant_data = quantiles_file2
            data = self.get_precalc_BW_data([surv], quant_data)
            if surv_idx == 0:
                coh_vals = data
            else:
                coh_vals = np.column_stack((coh_vals, data))


        return run_DF, coh_vals
    
    def get_multiCohort_Data(self, year, Surveys, size_range, start_Date=None):
        '''
        structure = [Region1[[surv1, sizes, dates], [surv2, sizes, dates]], Region2[[surv1, sizes, dates], [surv2, sizes, dates]]]
        example: The amount of grown in 14 days is 14 days*0.14 mm/day = 1.96 mm
        '''
        Growth_rate = self.growth_rate
#         valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['Survey'][r] in Surveys]
        total_surv = 0
        all_surveys = []
        for section in Surveys:
            total_surv += len(section)
            for surv in section:
                all_surveys.append(surv)
        coh_count = np.zeros((len(self.poly_names),total_surv),np.float64)
        coh_vol = np.zeros((len(self.poly_names), total_surv),np.float64)
        coh_density = np.zeros((len(self.poly_names),total_surv),np.float64)
        coh_abundance = np.zeros((len(self.poly_names),total_surv),np.float64)
#         coh_dates = np.zeros((len(self.poly_names),total_surv),dtype=object)
#         coh_sizes = np.zeros((len(self.poly_names),total_surv),dtype=object)
        
        file_sources = [self.obs_df1, self.obs_df2]
        
        for obs_idx, obs_file in enumerate(file_sources):
            dates, sizes = self.get_dates_and_sizes(obs_file, year, Surveys[obs_idx], size_range, Growth_rate)
            if obs_idx == 0:
                coh_dates = dates
                coh_sizes = sizes
            else:
                coh_dates = np.column_stack((coh_dates, dates))
                coh_sizes = np.column_stack((coh_sizes, sizes))
        
        surv_split = len(Surveys[0])
        for reg_idx, reg in enumerate(coh_dates):
            if not isinstance(reg[surv_split][0], float) and not isinstance(reg[surv_split-1][1], float):
                hatch_date = reg[0][0] #get hatch date if available
                time_elapsed = reg[surv_split][0] - reg[surv_split-1][1]
#                 growth = time_elapsed.days * 0.14 #Growth Rate
                growth = time_elapsed.days * Growth_rate #Growth Rate
                growth_round = int(math.ceil(growth))
                size_Range_offset = coh_sizes[reg_idx][surv_split-1][0] - coh_sizes[reg_idx][surv_split][0]
                total_shift = growth_round + size_Range_offset
                for surv_idx, size_range in enumerate(coh_sizes[reg_idx]):
                    if surv_idx >= surv_split:
                        size_range[0] += total_shift
                        size_range[1] += total_shift
                        coh_sizes[reg_idx][surv_idx] = size_range[:]
            if not isinstance(reg[surv_split][0], float) and isinstance(reg[surv_split-1][1], float): #if cur data is good but prev is NAN
                time_elapsed = reg[surv_split][0] - hatch_date
                growth = time_elapsed.days * Growth_rate
                growth_round = int(math.ceil(growth))
                size_Range_offset = coh_sizes[reg_idx][surv_split-1][0] - coh_sizes[reg_idx][surv_split][0]
                total_shift = growth_round + size_Range_offset
                for surv_idx, size_range in enumerate(coh_sizes[reg_idx]):
                    if surv_idx >= surv_split:
                        size_range[0] += total_shift
                        size_range[1] += total_shift
                        coh_sizes[reg_idx][surv_idx] = size_range[:]
        
    
        for reg_idx, region in enumerate(self.poly_names): #go by each region
            #find index where the year, region, and listed surveys
            for surv_idx, surv in enumerate(all_surveys):
                if surv_idx < surv_split:
                    self.obs_df = file_sources[0]
                else:
                    self.obs_df = file_sources[1]
            
                in_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['lfs_region'][r] == region and self.obs_df['Survey'][r] == surv]
                if start_Date != None:
                    in_idx = self.filter_by_startDate(in_idx, start_Date)
                for idx in in_idx:
                    cur_vol = self.obs_df['Volume'].values[idx]
                    if isinstance(coh_sizes[reg_idx][surv_idx], str):
                        fish_counts = self.countAllFishSizes(idx, self.obs_df)
                    else:
                        fish_counts = self.countSomeFishSizes(idx, coh_sizes[reg_idx][surv_idx], self.obs_df)    
                         
                    coh_count[reg_idx][surv_idx] += fish_counts
                    coh_vol[reg_idx][surv_idx] += cur_vol   
                     
        with open('Cohort_data_output_{0}.csv'.format(year), 'wb') as outtext:    
            outtext.write('region,survey,Date_Start,Date_End,year,size min,size max,fish count,volume per Survey,Density in {0} fish per m3,Region Volume,Reg Abundance\n'.format(self.density_units))
            for reg_idx, region in enumerate(self.poly_names):
                vol_file_idx = np.where(self.obs_static_vol['region_name'].values == region.replace('_',' '))[0][0]
                region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
                for surv_idx, surv_count in enumerate(coh_count[reg_idx]):
                    coh_density[reg_idx][surv_idx] = surv_count / coh_vol[reg_idx][surv_idx] 
                    coh_abundance[reg_idx][surv_idx] = coh_density[reg_idx][surv_idx] * region_vol
                    coh_abundance = np.nan_to_num(coh_abundance)
                    try:
                        outline = ','.join([str(r) for r in [region, surv_idx+1,coh_dates[reg_idx][surv_idx][0].strftime('%m/%d'),coh_dates[reg_idx][surv_idx][1].strftime('%m/%d'), year, coh_sizes[reg_idx][surv_idx][0], coh_sizes[reg_idx][surv_idx][1], surv_count, coh_vol[reg_idx][surv_idx], coh_density[reg_idx][surv_idx] * self.density_units, region_vol, coh_abundance[reg_idx][surv_idx], '\n']])
                    except AttributeError:
                        outline = ','.join([str(r) for r in [region, surv_idx+1,'nan','nan', year, coh_sizes[reg_idx][surv_idx][0],coh_sizes[reg_idx][surv_idx][1], surv_count, coh_vol[reg_idx][surv_idx], coh_density[reg_idx][surv_idx] * self.density_units, region_vol, coh_abundance[reg_idx][surv_idx], '\n']])
                    outtext.write(outline)

        return coh_abundance
    
    def get_Predicted_data(self, coh_surv_dates):
        pred_abun = np.empty_like(coh_surv_dates)
        
        for reg_idx, region in enumerate(self.poly_names):
            for surv_idx, surv in enumerate(pred_abun[reg_idx]):
                start_date = coh_surv_dates[reg_idx][surv_idx][0]
                if not isinstance(start_date, float):
                    start_date_str = dt.strftime(start_date, '%Y-%m-%d')
                    in_idx = [r for r, date in enumerate(self.pred_data.ix[:,1].values) if date.strip() == start_date_str and self.pred_data.ix[:,2].values[r] == reg_idx]
                    print in_idx, start_date_str
                    if len(in_idx) == 0:
                        pred_abun[reg_idx][surv_idx] = 0
                    else:
                        pred_abun[reg_idx][surv_idx] = self.pred_data.ix[:,3].values[in_idx][0]
                        print pred_abun[reg_idx][surv_idx]
                else:
                    pred_abun[reg_idx][surv_idx] = 0
        return pred_abun
    
    def countAllFishSizes(self, index, obs_data):
        '''add fish at each mm size to one total
        '''
        size_readings = [r for r in obs_data.keys() if 'mm' in r]
        total = 0
        for size in size_readings:
            total += obs_data[size][index]
        return total
    
    def countSomeFishSizes(self, index, size_range, obs_data):
        '''add fish at specified mm sizes to one total
        '''
        total = 0
        min = size_range[0]
        max = size_range[1]
        for size in range(min, max+1):
            key = str(size) + 'mm'
            if key in obs_data.columns.values:
                total += obs_data[key][index]
            else:
                print 'Invalid Size of', key
                continue
        return total
    
    def get_Plot_Scale(self, data, plotType):
        
        if plotType == 'BoxWhisker':
            meds = []
            for region in data:
                for surv in region:
                    meds.append(surv['med'])
            max_med = max(meds)
            len_max = (len(str(max_med).split('.')[0]) - 2) * -1
            scaler = round(max_med, len_max)
            self.plottype = 'BoxWhisker'
            
        elif plotType == 'Bar':
            maxes = []
            for region in data:
                maxes.append(max(region))
            largest_max = max(maxes)
            len_max = (len(str(largest_max).split('.')[0]) - 2) * -1
            scaler = round(largest_max, len_max)
            self.plottype = 'Bar'
            
        elif plotType == 'Log':
            maxes = []
            for region in data:
                maxes.append(max(region))
            largest_max = max(maxes)
            len_max = (len(str(largest_max).split('.')[0]) - 2) * -1
            if str(largest_max).split('.')[0][:len_max] != 10:
                num_zero = (len_max * -1) + 1
            scaler = int('10' + '0'*num_zero)
            self.plottype = 'Log'
            
        return scaler
    
    def Abundance_to_Density(self, obs_Data, size_range):
        '''
        Converts Abundance to density (fish per 10,000 m3)
        also writes out a csv file for density stats for Precalc data
        '''
        if self.datatype == 'Precalculated':
            obs_density = np.empty_like(obs_Data)
            for i, reg in enumerate(self.poly_names):
                vol_file_idx = np.where(self.obs_static_vol['region_name'].values == reg.replace('_',' '))[0][0]
                region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
                for s, surv in enumerate(obs_Data[i]):
                    obs_density[i][s] = {}
                    for key in surv.keys():
                        obs_density[i][s][key] = (surv[key] / region_vol) * self.density_units
            self.write_Box_Stats(obs_density, 'Density_BoxWhisker_Stats_{0}_{1}mm-{2}mm.csv'.format(self.year, size_range[0], size_range[1]))
             
        elif self.datatype == 'Observed':
            obs_density = np.empty_like(obs_Data)
            for i, reg in enumerate(self.poly_names):
                vol_file_idx = np.where(self.obs_static_vol['region_name'].values == reg.replace('_',' '))[0][0]
                region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
                for s, surv in enumerate(obs_Data[i]):
                    obs_density[i][s] = (surv / region_vol) * self.density_units
                    
        else:
            print 'Undefined type for converting data.'
            print 'Entered type: {0}. Continuing as if Observed data.'.format(self.datatype)
            print 'No promise this will work correctly.'
            self.datatype = 'Observed'
            obs_density = self.Abundance_to_Density(obs_Data, size_range) #run function again as observed
           
        return obs_density
    
    def get_file_BW_data(self,year,size_range):
        '''
        Get Box whisker data from long file
        Under Construction, do not use yet
        '''
#         valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date in years]
#          
        reg_abundance = np.zeros((len(self.poly_names)),dtype=object)
        obs_count = np.zeros((len(self.poly_names)),dtype=object)
        obs_vol = np.zeros((len(self.poly_names)),dtype=object)
        obs_density = np.zeros((len(self.poly_names)),dtype=object)

        
        for reg_idx ,reg in enumerate(self.poly_names):
#             print reg
            valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['lfs_region'].values[r] == reg]
#             valid_idx = [r for r, obsreg in enumerate(self.obs_df['lfs_region'].values) if obsreg == reg ]
            yearly_surveys= list(set(self.obs_df['Survey'].values[valid_idx]))
            
            reg_abundance[reg_idx] = np.zeros(len(yearly_surveys))
            obs_count[reg_idx] = np.zeros(len(yearly_surveys))
            obs_vol[reg_idx] = np.zeros(len(yearly_surveys))
            obs_density[reg_idx] = np.zeros(len(yearly_surveys))
            vol_file_idx = np.where(self.obs_static_vol['region_name'].values == reg.replace('_',' '))[0][0]
            region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
            for i, v_idx in enumerate(valid_idx):
                if isinstance(size_range, str):
                    fish_counts = self.countAllFishSizes(v_idx, self.obs_df)
                else:
                    fish_counts = self.countSomeFishSizes(v_idx, size_range, self.obs_df)
                cur_survey = self.obs_df['Survey'].values[v_idx]
                survey_idx = yearly_surveys.index(cur_survey)
                obs_count[reg_idx][survey_idx] += fish_counts
                obs_vol[reg_idx][survey_idx] += self.obs_df['Volume'].values[i]
                obs_density[reg_idx][survey_idx] += fish_counts / self.obs_df['Volume'].values[i]
#                 print cur_survey, reg, fish_counts
                reg_abundance[reg_idx][survey_idx] += obs_density[reg_idx][survey_idx] * region_vol
        return reg_abundance
    
    def get_precalc_BW_data(self, surveys, obs_BW_file):
        '''
        reads in calculated trawl file and organizes it into arrays for Box whisker plots
        Also writes out csv file for easy stat reading
        '''

        region_stats = np.zeros((len(self.poly_names), len(surveys)),dtype=object)

        for region in self.poly_names:
#             print region
            reg_idx = [r for r, reg in enumerate(obs_BW_file['region'].values) if reg == region.replace('_', ' ') and obs_BW_file['survey'].values[r] in surveys]

            for idx in reg_idx:
                cur_reg = obs_BW_file['region'].values[idx].replace(' ', '_')
                reg_idx = self.poly_names.index(cur_reg)
                cur_surv = obs_BW_file['survey'].values[idx]
                surv_idx = surveys.index(cur_surv)
                
                item = {}
                item["med"] = obs_BW_file['q50'].values[idx]
                item["q1"] = obs_BW_file['q25'].values[idx]
                item["q3"] = obs_BW_file['q75'].values[idx]
                item["whislo"] = obs_BW_file['q5'].values[idx]
                item["whishi"] = obs_BW_file['q95'].values[idx]
                region_stats[reg_idx][surv_idx] = item
                
        return region_stats
        self.write_Box_Stats(region_stats, 'BoxWhisker_Stats_{0}.csv'.format(self.year))
        
    
    def write_Box_Stats(self, stats, filename):
        with open(filename, 'wb') as g:
            g.write('region,survey,q5,q25,q50,q75,q95\n')
            for i, reg in enumerate(self.poly_names):
                for s, surv in enumerate(stats[i]):
                    g.write('{0},{1},{2},{3},{4},{5},{6}\n'.format(reg, s+1, surv['whislo'], surv['q1'], surv['med'], surv['q3'], surv['whishi']))
    
    def offset_plots(self, barxy, barboxsize):
        adjust = barboxsize[1] / 2 + 100
        adj_barxy_up = np.empty_like(barxy)
        adj_barxy_down = np.empty_like(barxy)
        for reg_idx, region_xy in enumerate(barxy):
            adj_barxy_up[reg_idx] = [region_xy[0], region_xy[1] + adjust]
            adj_barxy_down[reg_idx] = [region_xy[0], region_xy[1] - adjust]
            
        return adj_barxy_up, adj_barxy_down
### ~~~~~~~~~~~~~~~~ CONTROL FUNCTIONS ~~~~~~~~~~~~~~~~ ###

    def make_Obs_Barplot(self, longfile_path, figname, size_range, Surveys,static_volumes_file):
        '''
        Creates a bar plot of the Abundance for a particular year.
         many surveys is untested and may look really ugly. Consider keeping 9 surveys max.
        
        '''
        self.check_runtype()
        self.datatype = 'Observed' #set this parameter for run specific functions
        self.obs_df = pd.read_csv(longfile_path, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        
        bars = []
        for num in Surveys:
            bars.append('Survey {0}'.format(num))
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
        plot_types = ['Density', 'Abundance']
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)
            leg_args = {'ylabel':plot_type,
                        'bars':bars,
                        'max':''}
            
#             if leg_args['ylabel'] == 'Density':
#                 leg_args['max'] = self.max_den[self.year]
#             elif leg_args['ylabel'] == 'Abundance':
#                 leg_args['max'] = self.max_ab[self.year]
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('{0} Fish Abundance {1} '.format(self.runtype.upper(), self.year))
                
            
#             plt.title('Observed {0} {1}'.format(leg_args['ylabel'], self.year))
            
            
            # read observed counts
            obs_data = self.get_Obs_data(self.year, Surveys, size_range)
            
            if leg_args['ylabel'] == 'Density':
                obs_data = self.Abundance_to_Density(obs_data, size_range) #convert abundance data to density
            
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            labels = self.findNoData(Surveys, self.obs_df) #find correct labels for surveys with no data
            leg_args['max'] = self.get_Plot_Scale(obs_data, 'Bar')
            leg_args['PlotType'] = 'Bar'
            print leg_args['max'], obs_data
            Longfin_Plot_Utils.plot_bars(ax, fig, obs_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return


            
    def make_precalc_BoxWhiskerPlot(self, data_path, figname, size_range, Surveys, static_volumes_file):
        '''
        Plots Box Whisker plots for observed data in trawl files
        data is precalculated and does NOT come from long file, but is possible
        ylabel can be set to "Abundance" or "Density"
        '''
        self.check_runtype()
        self.datatype = 'Precalculated' #set this parameter for run specific functions
        self.obs_BW_file = pd.read_csv(data_path, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        boxes = []
        
        for num in Surveys:
            boxes.append('Survey {0}'.format(num))

        plot_types = ['Density', 'Abundance']
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)
            leg_args = {'ylabel':plot_type,
                        'boxes':boxes,
                        'max':''}
            
#             if leg_args['ylabel'] == 'Density':
#                 leg_args['max'] = self.max_den[self.year]
#             elif leg_args['ylabel'] == 'Abundance':
#                 leg_args['max'] = self.max_ab[self.year]
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('{0} Fish Abundance {1} '.format(self.runtype.upper(), self.year))
        
    #         if leg_args['ylabel'] == 'Density':
    #             leg_args['max'] = self.max_den[self.year]
    #         elif leg_args['ylabel'] == 'Abundance':
    #             leg_args['max'] = self.max_ab[self.year]

        
#             plt.title('Observed {0} {1}'.format(leg_args['ylabel'], self.year))
            barboxsize = [10000.,10000.]
            
            obs_data = self.get_precalc_BW_data(Surveys, self.obs_BW_file)
            barxy = self.findSiteLoc(self.poly_names)
            labels = self.findNoData(Surveys, self.obs_df)
            
            if leg_args['ylabel'] == 'Density':
                obs_data = self.Abundance_to_Density(obs_data, size_range) #convert abundance data to density
                
            leg_args['max'] = self.get_Plot_Scale(obs_data, 'BoxWhisker')
            leg_args['PlotType'] = 'BoxWhisker'
            Longfin_Plot_Utils.plot_boxes(ax, fig, obs_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
    
            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_Cohort_Plot(self, longfile_path, figname, size_range, Surveys,static_volumes_file):
        '''UNDER CONSTRUCTION
        Create a plot for cohort growth. cohort growth shows a gradual increase of .14 * days between surveys
        this growth is added to the size range, progressively growing as time goes on.
        '''
        self.check_runtype()
        self.datatype = 'Observed' #set this parameter for run specific functions
        self.obs_df = pd.read_csv(longfile_path, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        self.growth_rate = .2
        
        bars = []
        for num in Surveys:
            bars.append('Survey {0}'.format(num))
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
#         plot_types = ['Density', 'Abundance']
        plot_types = ['Abundance'] #Just abundance atm...
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)
            leg_args = {'ylabel':plot_type,
                        'bars':bars,
                        'max':''}
            
#             if leg_args['ylabel'] == 'Density':
#                 leg_args['max'] = self.max_den[self.year]
#             elif leg_args['ylabel'] == 'Abundance':
#                 leg_args['max'] = self.max_ab[self.year]
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('Longfin Smelt {0}mm to {1}mm {2} Cohort {3} {4}'.format(size_range[0], size_range[1], self.runtype.upper(), plot_type, self.year))
                
            
#             plt.title('Observed {0} {1}'.format(leg_args['ylabel'], self.year))
            
            
            # read observed counts
            coh_data = self.get_Cohort_Data(self.year, Surveys, size_range)
            
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
            
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            labels = self.findNoData(Surveys, self.obs_df) #find correct labels for surveys with no data
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'Bar')
            leg_args['PlotType'] = 'Bar'
            Longfin_Plot_Utils.plot_bars(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
            
            xloc = ax.get_xlim()[0] + ((ax.get_xlim()[1] - ax.get_xlim()[0]) * .65) 
            yloc = ax.get_ylim()[0] + ((ax.get_ylim()[1] - ax.get_ylim()[0]) * .1) 
            
            ax.text(xloc, yloc, 'Growth Rate = {0} mm/Day'.format(self.growth_rate))

            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_MultiCohort_Bar_Plot(self, longfile_path1, longfile_path2, figname, size_range, static_volumes_file):
        '''
        Create a plot for cohort growth. cohort growth shows a gradual increase between surveys
        this growth is added to the size range, progressively growing as time goes on.
        includes 2 data sources
        '''
        self.check_runtype()
        self.check_multisurveys()
        self.datatype = 'Observed' #set this parameter for run specific functions
        self.obs_df1 = pd.read_csv(longfile_path1, parse_dates=True)
        self.obs_df2 = pd.read_csv(longfile_path2, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        self.growth_rate = .2
        
        bars = []
        for num in self.multisurveys[0]:
            bars.append('{0} {1}'.format(os.path.basename(longfile_path1).split('_')[0], num))
        for num in self.multisurveys[1]:
            bars.append('{0} {1}'.format(os.path.basename(longfile_path2).split('_')[0], num))
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
#         plot_types = ['Density', 'Abundance']
        plot_types = ['Abundance'] #Just abundance atm...
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)
            leg_args = {'ylabel':plot_type,
                        'bars':bars,
                        'max':''}
            
#             if leg_args['ylabel'] == 'Density':
#                 leg_args['max'] = self.max_den[self.year]
#             elif leg_args['ylabel'] == 'Abundance':
#                 leg_args['max'] = self.max_ab[self.year]
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('Longfin Smelt {0}mm to {1}mm Cohort {2} {3} '.format(size_range[0], size_range[1], plot_type, self.year))
                
            
            
            
            # read observed counts
#             self.obs_df =  self.obs_df1 #set this just for temp reasons
            coh_data = self.get_multiCohort_Data(self.year, self.multisurveys, size_range)
            
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
            
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            
            self.obs_df =  self.obs_df1
            labels1 = self.findNoData(self.multisurveys[0], self.obs_df) #find correct labels for surveys with no data
            self.obs_df =  self.obs_df2 #set this just for temp reasons
            labels2 = self.findNoData(self.multisurveys[1], self.obs_df)
            labels = np.column_stack((labels1, labels2))
            
#             leg_args['max'] = self.get_Plot_Scale(coh_data, 'Log')
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'Bar')
            leg_args['PlotType'] = 'Log'
            Longfin_Plot_Utils.plot_bars(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
            xloc = ax.get_xlim()[0] + ((ax.get_xlim()[1] - ax.get_xlim()[0]) * .65) 
            yloc = ax.get_ylim()[0] + ((ax.get_ylim()[1] - ax.get_ylim()[0]) * .1) 
            
            ax.text(xloc, yloc, 'Growth Rate = {0} mm/Day'.format(self.growth_rate))

            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_ST_MultiCohort_Bar_Plot(self, longfile_path1, longfile_path2, figname, size_range, static_volumes_file, start_Date):
        '''
        Create a plot for cohort growth. Data before start date is ommited.
        cohort growth shows a gradual increase s between surveys
        this growth is added to the size range, progressively growing as time goes on.
        includes 2 data sources
        '''
        self.check_runtype()
        self.check_multisurveys()
        self.datatype = 'Observed' #set this parameter for run specific functions
        self.obs_df1 = pd.read_csv(longfile_path1, parse_dates=True)
        self.obs_df2 = pd.read_csv(longfile_path2, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        self.growth_rate = .2
        
        bars = []
        for num in self.multisurveys[0]:
            bars.append('{0} {1}'.format(os.path.basename(longfile_path1).split('_')[0], num))
        for num in self.multisurveys[1]:
            bars.append('{0} {1}'.format(os.path.basename(longfile_path2).split('_')[0], num))
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
#         plot_types = ['Density', 'Abundance']
        plot_types = ['Abundance'] #Just abundance atm...
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)
            leg_args = {'ylabel':plot_type,
                        'bars':bars,
                        'max':''}
            
#             if leg_args['ylabel'] == 'Density':
#                 leg_args['max'] = self.max_den[self.year]
#             elif leg_args['ylabel'] == 'Abundance':
#                 leg_args['max'] = self.max_ab[self.year]
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('Longfin Smelt {0}mm to {1}mm Cohort {2} {3} '.format(size_range[0], size_range[1], plot_type, self.year))
                
            
            
            
            # read observed counts
#             self.obs_df =  self.obs_df1 #set this just for temp reasons
            coh_data = self.get_multiCohort_Data(self.year, self.multisurveys, size_range, start_Date=start_Date)
            
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
            
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            
            self.obs_df =  self.obs_df1
            labels1 = self.findNoData(self.multisurveys[0], self.obs_df) #find correct labels for surveys with no data
            self.obs_df =  self.obs_df2 #set this just for temp reasons
            labels2 = self.findNoData(self.multisurveys[1], self.obs_df)
            labels = np.column_stack((labels1, labels2))
            
#             leg_args['max'] = self.get_Plot_Scale(coh_data, 'Log')
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'Bar')
            leg_args['PlotType'] = 'Log'
            Longfin_Plot_Utils.plot_bars(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
            
            xloc = ax.get_xlim()[0] + ((ax.get_xlim()[1] - ax.get_xlim()[0]) * .65) 
            yloc = ax.get_ylim()[0] + ((ax.get_ylim()[1] - ax.get_ylim()[0]) * .1) 
            
            ax.text(xloc, yloc, 'Growth Rate = {0} mm/Day \nStart Date = {1}'.format(self.growth_rate, start_Date.strftime('%m-%d-%Y')))

            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_Chronological_MultiCohort_Bar_Plot(self, longfile_path1, longfile_path2, figname, size_range, static_volumes_file):
        '''
        Create a plot for cohort growth sorted chronologically. cohort growth shows a gradual increase between surveys
        this growth is added to the size range, progressively growing as time goes on.
        includes 2 data sources
        '''
        self.check_runtype()
        self.check_multisurveys()
        self.datatype = 'Observed' #set this parameter for run specific functions
        self.obs_df1 = pd.read_csv(longfile_path1, parse_dates=True)
        self.obs_df2 = pd.read_csv(longfile_path2, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        
        self.growth_rate = 0.2
        
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
#         plot_types = ['Density', 'Abundance']
        plot_types = ['Abundance'] #Just abundance atm...
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)

            run_DF, coh_data = self.get_Chronological_Multicohort_Data(self.year, self.multisurveys, size_range)
            
            labels = np.chararray((len(self.poly_names), len(run_DF[1])))
            labels[:] = 'X'
                
            bars = []
            for file_idx, file_num in enumerate(run_DF[1]):
                if file_num == 0:
                    bars.append('{0} {1}'.format(os.path.basename(longfile_path1).split('_')[0], run_DF[2][file_idx]))
                    cur_labs = self.findNoData([run_DF[2][file_idx]], self.obs_df1)
# 
#                     for lab_idx in range(len(labels[0])):
#                         labels[lab_idx][file_idx] = cur_labs[lab_idx][0]
                else:
                    bars.append('{0} {1}'.format(os.path.basename(longfile_path2).split('_')[0], run_DF[2][file_idx]))
                    cur_labs = self.findNoData([run_DF[2][file_idx]], self.obs_df2)
                    
                for lab_idx in range(len(labels)):
                    labels[lab_idx][file_idx] = cur_labs[lab_idx][0]
                    print self.poly_names[lab_idx], file_idx, cur_labs[lab_idx][0]
                    
            leg_args = {'ylabel':plot_type,
            'bars':bars,
            'max':''}


            
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('Longfin Smelt {0}mm to {1}mm Chronological Cohort {2} {3} '.format(size_range[0], size_range[1], plot_type, self.year))
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
                
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site

            
#             leg_args['max'] = self.get_Plot_Scale(coh_data, 'Log')
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'Bar')
            leg_args['PlotType'] = 'Log'
            Longfin_Plot_Utils.plot_bars(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
            xloc = ax.get_xlim()[0] + ((ax.get_xlim()[1] - ax.get_xlim()[0]) * .65) 
            yloc = ax.get_ylim()[0] + ((ax.get_ylim()[1] - ax.get_ylim()[0]) * .1) 
            
            ax.text(xloc, yloc, 'Growth Rate = {0} mm/Day'.format(self.growth_rate))

            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_Chronological_MultiCohort_BoxWhisker_Plot(self, longfile_path1, longfile_path2, quantiles_path1, quantiles_path2, figname, size_range, static_volumes_file):
        '''
        Create a plot for cohort growth sorted chronologically. cohort growth shows a gradual increase between surveys
        this growth is added to the size range, progressively growing as time goes on.
        includes 4 data sources, longfiles to get dates and the data from precalc files.
        '''
        self.check_runtype()
        self.check_multisurveys()
        self.datatype = 'Precalculated' #set this parameter for run specific functions
        self.obs_df1 = pd.read_csv(longfile_path1, parse_dates=True)
        self.obs_df2 = pd.read_csv(longfile_path2, parse_dates=True)
        self.quant_df1 = pd.read_csv(quantiles_path1, parse_dates = True)
        self.quant_df2 = pd.read_csv(quantiles_path2, parse_dates = True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        
        self.growth_rate = 0.2
        
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
#         plot_types = ['Density', 'Abundance']
        plot_types = ['Abundance'] #Just abundance atm...
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)

            run_DF, coh_data = self.get_Chronological_Multicohort_Boxwhisker_Data(self.year, self.multisurveys, self.quant_df1, self.quant_df2)
            
            labels = np.chararray((len(self.poly_names), len(run_DF[1])))
            labels[:] = 'X'
                
            boxes = []
            for file_idx, file_num in enumerate(run_DF[1]):
                if file_num == 0:
                    boxes.append('{0} {1}'.format(os.path.basename(longfile_path1).split('_')[0], run_DF[2][file_idx]))
                    cur_labs = self.findNoData([run_DF[2][file_idx]], self.quant_df1)
                else:
                    boxes.append('{0} {1}'.format(os.path.basename(longfile_path2).split('_')[0], run_DF[2][file_idx]))
                    cur_labs = self.findNoData([run_DF[2][file_idx]], self.quant_df2)
                    
                for lab_idx in range(len(labels)):
                    labels[lab_idx][file_idx] = cur_labs[lab_idx][0]
                    print self.poly_names[lab_idx], file_idx, cur_labs[lab_idx][0]
                    
            leg_args = {'ylabel':plot_type,
            'boxes':boxes,
            'max':''}


            
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('Longfin Smelt {0}mm to {1}mm Chronological Cohort {2} {3} '.format(size_range[0], size_range[1], plot_type, self.year))
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
                
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site


#             self.obs_df =  self.obs_df1
#             labels1 = self.findNoData(self.multisurveys[0], obs_data) #find correct labels for surveys with no data
#             self.obs_df =  self.obs_df2 #set this just for temp reasons
#             labels2 = self.findNoData(self.multisurveys[1], obs_data)
#             labels = np.column_stack((labels1, labels2))
            
#             leg_args['max'] = self.get_Plot_Scale(coh_data, 'Log')
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'BoxWhisker')
            leg_args['PlotType'] = 'BoxWhisker'
            Longfin_Plot_Utils.plot_boxes(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
#             xloc = ax.get_xlim()[0] + ((ax.get_xlim()[1] - ax.get_xlim()[0]) * .65) 
#             yloc = ax.get_ylim()[0] + ((ax.get_ylim()[1] - ax.get_ylim()[0]) * .1) 
#             ax.text(xloc, yloc, 'Growth Rate = {0} mm/Day'.format(self.growth_rate))

            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_MultiCohort_BoxWhisker_Plot(self, longfile_path1, longfile_path2, figname, size_range, static_volumes_file):
        '''
        Create a box whisker plot for cohort growth. cohort growth shows a gradual increase of .14-.2 * days between surveys
        this growth is added to the size range, progressively growing as time goes on.
        include 2 longfile data sources as the observed. SLS and 20mm, chronologically.
        size is mantained if earlier surveys don't include an area
        Size range needs to come from a list of two lists, i.e. [[1, 5], [4, 10]]..
        if there is only one data source, use make_precalc_BoxWhiskerPlot() instead
        '''
        self.check_runtype()
        self.check_multisurveys()
        self.datatype = 'Precalculated' #set this parameter for run specific functions
        self.obs_BW_file1 = pd.read_csv(longfile_path1, parse_dates=True)
        self.obs_BW_file2 = pd.read_csv(longfile_path2, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        
        #make labels of all surveys from sources for legend
        boxes = []
        for num in self.multisurveys[0]:
            boxes.append('{0} {1}'.format(os.path.basename(longfile_path1).split('_')[0], num))
        for num in self.multisurveys[1]:
            boxes.append('{0} {1}'.format(os.path.basename(longfile_path2).split('_')[0], num))
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
#         plot_types = ['Density', 'Abundance']
        plot_types = ['Abundance'] #Just abundance atm...
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)
            leg_args = {'ylabel':plot_type,
                        'boxes':boxes,
                        'max':''}
            
            #use this to set to a hardwired max for the plot. Otherwise, the max value will be used
            # so that the highest median will be displayed
#             if leg_args['ylabel'] == 'Density':
#                 leg_args['max'] = self.max_den[self.year]
#             elif leg_args['ylabel'] == 'Abundance':
#                 leg_args['max'] = self.max_ab[self.year]

            # Set Plot title. Density will need adjustment if implemented. 
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('Longfin Smelt {0}mm to {1}mm Cohort {2} {3} '.format(size_range[0], size_range[1], plot_type, self.year))
            
            # read observed counts from files, and then stack on top of each other
            self.obs_BW_file = self.obs_BW_file1
            coh_data1 = self.get_precalc_BW_data(self.multisurveys[0], self.obs_BW_file)
            self.obs_BW_file = self.obs_BW_file2
            coh_data2 = self.get_precalc_BW_data(self.multisurveys[1], self.obs_BW_file)
            coh_data = np.column_stack((coh_data1, coh_data2))
            
            #convert Density data to abundance if needed
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
            
            #get the xy locations for each site
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            
            #find the labels for each data source, and then merge the two arrays for all data
            self.obs_BW_file = self.obs_BW_file1
            labels1 = self.findNoData(self.multisurveys[0], self.obs_BW_file) #find correct labels for surveys with no data
            self.obs_BW_file = self.obs_BW_file2 #set this just for temp reasons
            labels2 = self.findNoData(self.multisurveys[1], self.obs_BW_file)
            labels = np.column_stack((labels1, labels2))
            leg_args['PlotType'] = 'Log'
            
            #Get the plot scale. Max is determined by the highest median here
            leg_args['max'] = self.get_Plot_Scale(coh_data, leg_args['PlotType'])
            
            #set the plot type. Could have functionality for plot scaling, but for now doesn't do anything
            
            
            #Plot the data and save
            Longfin_Plot_Utils.plot_boxes(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), leg_args['PlotType'], '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_PredvsObs_MultiCohort_Plot(self, longfile_path1, longfile_path2, pred_file, figname, size_range,static_volumes_file):
        '''
        Create a plot for predicted vs observed vs predicted cohort growth. cohort growth shows a gradual increase of .14 - .2 * days between surveys
        this growth is added to the size range, progressively growing as time goes on.
        include 2 longfile data sources as the observed. SLS and 20mm, chronologically.
        Predicted data comes in from *_abundance.csv file
        size is mantained if earlier surveys don't include an area
        Size range needs to come from a list of two lists, i.e. [[1, 5], [4, 10]]..
        Predicted data is determined by the date of the start of each surveys
        '''
        self.check_runtype()
        self.check_multisurveys()
        self.datatype = 'Observed' #set this parameter for run specific functions
        self.obs_df1 = pd.read_csv(longfile_path1, parse_dates=True)
        self.obs_df2 = pd.read_csv(longfile_path2, parse_dates=True)
        self.pred_data = pd.read_csv(pred_file, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        
        #make labels of all surveys from sources for legend
        bars = []
        for num in self.multisurveys[0]:
            bars.append('{0} {1}'.format(os.path.basename(longfile_path1).split('_')[0], num))
        for num in self.multisurveys[1]:
            bars.append('{0} {1}'.format(os.path.basename(longfile_path2).split('_')[0], num)) ##set these to dates?
            
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
#         plot_types = ['Density', 'Abundance']
        plot_types = ['Abundance'] #Just abundance atm...
        
        for plot_type in plot_types:
            
            fig, ax = Longfin_Plot_Utils.draw_water_and_polys(self.grd, self.plot_poly_dict, self.xylims)
            leg_args = {'ylabel':plot_type,
                        'bars':bars,
                        'max':''}
            #set these to 'hard code' the legend plot maxes. Otherwise, the max value will be used
#             if leg_args['ylabel'] == 'Density':
#                 leg_args['max'] = self.max_den[self.year]
#             elif leg_args['ylabel'] == 'Abundance':
#                 leg_args['max'] = self.max_ab[self.year]

            #set the title of the plot. Density will need to reworked a bit if implemented
            if leg_args['ylabel'] == 'Density':
                plt.title('{0} Estimated Fish per {1} cubic meter {2}'.format(self.runtype.upper(), int(self.density_units), self.year))
            elif leg_args['ylabel'] == 'Abundance':
                plt.title('Longfin Smelt {0}mm to {1}mm Cohort {2} {3} '.format(size_range[0], size_range[1], plot_type, self.year))

            # read observed counts
            #Get the data for the two obs data sources. Function takes them both in, with the surveys, and returns a single array of data
            coh_data = self.get_multiCohort_Data(self.year, self.multisurveys, size_range)
            
            #get the start and end date of each cohort suvery. Returns a list of dates for each region, and survey.
            coh_surv_dates = self.get_Cohort_start_dates(self.year, self.multisurveys, size_range)
            
            #use the dataes from above to get the values for each predicted data region/survey
            pred_data = self.get_Predicted_data(coh_surv_dates)
            
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
            
            #Gets the XY locations for each plot, then shifts them to accommodate two plots stacked on top of each other
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            barxy_up, barxy_down = self.offset_plots(barxy, barboxsize) 
            
            #get labels for missing data. Pred data cannot have missing labels, so make a dummy set that is all blank.
            self.obs_df =  self.obs_df1
            labels1 = self.findNoData(self.multisurveys[0], self.obs_df) #find correct labels for surveys with no data
            self.obs_df =  self.obs_df2 #set this just for temp reasons
            labels2 = self.findNoData(self.multisurveys[1], self.obs_df)
            coh_labels = np.column_stack((labels1, labels2))
            self.obs_df = self.pred_data
            pred_labels = np.empty_like(pred_data)
            pred_labels[:] = ''
            
            
#             leg_args['max'] = self.get_Plot_Scale(coh_data, 'Log')
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'Bar')
            
            #used for future labels. Plots currently too busy to be any use.
            leg_args['obspred_label'] = 'Obs'
            leg_args['PlotType'] = 'Bar'
            
            Longfin_Plot_Utils.plot_bars(ax, fig, coh_data, barxy_down, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=coh_labels)
            leg_args['obspred_label'] = 'Pred'
            Longfin_Plot_Utils.plot_bars(ax, fig, pred_data, barxy_up, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=pred_labels)
            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return

    
    def plot_precalc_Boxwhisker(self, obs_data, fig_name):
        '''Structure is a 4 len list for each region in self.poly
            list contains averaged q5, q25, q50, q75, q95
            makes a simple box whisker plt, but not on a map. Under Construction
        '''
        stats = []
        fig = plt.figure(figsize=[11,7])
        ax = fig.add_subplot(111)
        for region_stats in obs_data:
            item = {}
            item["med"] = region_stats[2]
            item["q1"] = region_stats[1]
            item["q3"] = region_stats[3]
            item["whislo"] = region_stats[0]
            item["whishi"] = region_stats[4]
            stats.append(item)
        ax.bxp(stats, showfliers=False)
        plt.savefig(fig_name, dpi=900, facecolor='white',
                    bbox_inches='tight')
            
        print 'end'
        

    def findSiteLoc(self, site_names):
        # Reads dictionary for easting, northing and returns those coordinates.
        
        barxy = np.zeros((len(site_names),2),np.float64)
        for s,site in enumerate(site_names):
            barxy[s] = self.utm_dict[site]
        
        return barxy


if __name__ == '__main__':
    # test for single predicted distribution plot

    obs_bar = False
    obs_boxwhisker = False
    cohort = False
    multicohort_bar = True
    multicohort_boxwhisker = False
    pred_vs_obs_multicohort = False
    ST_multicohort_bar = False
    Chron_multicohort_bar = False
    Chron_multicohort_Boxwhisker = False

    year = 2012 #keep to one year for now, multiyear support coming
    size_range = [6, 10] #inclusive range for the mm values. so min and max values are included in totals
    surveys = [3,4,5,6]

    run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
    grd_file = os.path.join(run_dir, 'ptm.grd')
    cbm = LongfinMaps(run_dir, grd_file, year)
#     bm_inputs = cbm.get_inputs()
    fig_dir = 'Multicohort_plots'
    if not os.path.isdir(fig_dir):
        os.mkdir(fig_dir)
    
    runtype = 'sls' #sls or 20mm supported. Changes in Density calcs and titles
    
    if obs_bar:
        figname = os.path.join(fig_dir, 'obs_Bar_Plots')
        obs_data = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.runtype = runtype
        cbm.make_Obs_Barplot(obs_data, figname, size_range, surveys, static_volumes)
    if obs_boxwhisker:
        figname = os.path.join(fig_dir, 'Cohort_Box_Whisker')
        obs_data = r"J:\Longfin\bar_plots\SLS_quantiles_6mm-8mm_2012.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.runtype = runtype
        cbm.make_precalc_BoxWhiskerPlot(obs_data, figname, size_range, surveys, static_volumes)
    if cohort:
        figname = os.path.join(fig_dir, 'Cohort_Plots')
        obs_data = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.runtype = runtype
        cbm.make_Cohort_Plot(obs_data, figname, size_range, surveys, static_volumes)
    if multicohort_bar:
        figname = os.path.join(fig_dir, 'Extended_Cohort_BarPlots')
        obs_data1 = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
        obs_data2 = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.multisurveys = [[3,4,5,6], [2,3,4,5,6,7,8,9]]
        cbm.runtype = 'sls' #set one the density multiplier
        cbm.make_MultiCohort_Bar_Plot(obs_data1, obs_data2, figname, size_range, static_volumes)
    if multicohort_boxwhisker:
        figname = os.path.join(fig_dir, 'Extended_Cohort_BoxPlots')
        obs_data1 = r"J:\Longfin\from_Ed\SLS_quantiles_12mm-16mm_2012-3-1_grow0.20_2012.csv"
        obs_data2 = r"J:\Longfin\from_Ed\20mm_quantiles_12mm-16mm_2012-3-1_grow0.20_2012.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.multisurveys = [[1,2,3,4,5,6], [1,2,3,4,5,6,7,8,9]]
        cbm.runtype = 'sls' #set one the density multiplier
        cbm.make_MultiCohort_BoxWhisker_Plot(obs_data1, obs_data2, figname, size_range, static_volumes)
    if pred_vs_obs_multicohort:
        figname = os.path.join(fig_dir, 'Suisun_Pred_Vs_Obs_Extended_Cohort_Plots')
        obs_data1 = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
        obs_data2 = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        pred_data = r"J:\Longfin\bar_plots\higher_growth_6_to_10mm\Suisun_passive_abundance.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.multisurveys = [[1,2,3,4,5,6], [2,3,4,5,6,7,8,9]]
        cbm.runtype = 'sls' #set one the density multiplier
        cbm.make_PredvsObs_MultiCohort_Plot(obs_data1, obs_data2, pred_data, figname, size_range, static_volumes)
    if ST_multicohort_bar:
        figname = os.path.join(fig_dir, 'Starttime_Cohort_BarPlots')
        obs_data1 = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
        obs_data2 = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.multisurveys = [[3,4,5,6], [2,3,4,5,6,7,8,9]]
        cbm.runtype = 'sls' #set one the density multiplier
        start_Date = dt(2012, 3, 1)
        cbm.make_ST_MultiCohort_Bar_Plot(obs_data1, obs_data2, figname, size_range, static_volumes, start_Date)
    if Chron_multicohort_bar:
        figname = os.path.join(fig_dir, 'Chronological_Cohort_BarPlots')
        obs_data1 = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
        obs_data2 = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.multisurveys = [[3,4,5,6], [1,2,3,4,5,6,7,8,9]]
        cbm.runtype = 'sls' #set one the density multiplier
        cbm.make_Chronological_MultiCohort_Bar_Plot(obs_data1, obs_data2, figname, size_range, static_volumes)
    if Chron_multicohort_Boxwhisker:
        figname = os.path.join(fig_dir, 'Chronological_Cohort_BoxWhiskerPlots')
        obs_data1 = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
        obs_data2 = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        quantile_path1 = r"J:\Longfin\bar_plots\SLS_quantiles_12mm-16mm_2012-3-1_grow0.30_2012.csv"
        quantile_path2 = r"J:\Longfin\bar_plots\20mm_quantiles_12mm-16mm_2012-3-1_grow0.30_2012.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.multisurveys = [[1,2,3,4,5,6], [1,2,3,4,5,6,7,8,9]]
        cbm.runtype = 'sls' #set one the density multiplier
        cbm.make_Chronological_MultiCohort_BoxWhisker_Plot(obs_data1, obs_data2, quantile_path1, quantile_path2, figname, size_range, static_volumes)

