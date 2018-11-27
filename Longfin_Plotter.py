# Use for plotting SLS and 20mm survey data

import os.path
import csv
import numpy as np
from scipy import stats
import pandas as pd
import pylab
import matplotlib.pyplot as plt
import pdb
from datetime import datetime as dt
import math
# import camt_region_dicts
from stompy.grid import unstructured_grid
from rmapy.utils.gis import polygons_w_attributes_from_shp as polys_from_shp
import fish_ptm_results
import map_w_bars
import map_w_boxes
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
            'North_and_South_Forks_Mokelumne_River':[636706.2529748471,4220063.19969082],
            'South_Delta':[642592.4377057501,4189918.7990992256],
            'Cache_Slough_Complex':[615123.5756282026,4262158.33897849],
            'Confluence':[606111.7244591176,4214227.897524303],
            'Suisun_Bay':[588707.6453680942,4209584.007177471],
            'Carquinez_Strait':[571227.4604096551,4209182.676400363], 
            'Suisun_Marsh':[586210.4760883171,4225235.907484644],
            'San_Pablo_Bay':[553942.9282736651,4208647.568697553],
            'Petaluma':[540030.1280006216,4221490.153564978],
            'South_SF_Bay':[566963.8823753597,4165482.214004264],
            'Central_SF_Bay':[550375.5435882693,4192415.9683790025], 
            'Lower_South_SF_Bay':[586049.3904422284,4145683.2290003207], 
            'Napa_Sonoma':[556261.7283191724,4226662.861358802]}

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
        accepted_runtypes = {'sls':1000., 
                             '20mm':10000.}
        while self.runtype.lower() not in accepted_runtypes.keys():
            self.runtype = raw_input('Run type of {0} not support. Please enter a supported run type listed here: {1}'.format(self.runtype, ', '.join(accepted_runtypes.keys())))
        self.runtype = self.runtype.lower()
        self.density_units = accepted_runtypes[self.runtype]

    def findNoData(self, Surveys):
        regions = self.poly_names
        labels = np.chararray((len(regions), len(Surveys)))
        labels[:] = 'X'
        
        if self.datatype == 'Precalculated':
            valid_idx = [r for r, survey in enumerate(self.obs_BW_file['survey'].values) if survey in Surveys]
            for idx in valid_idx:
                if not np.isnan(self.obs_BW_file['q5'].values[idx]):
                    cur_region = self.obs_BW_file['region'][idx].replace(' ', '_')
                    reg_idx = regions.index(cur_region)
                    cur_surv = self.obs_BW_file['survey'][idx]
                    surv_idx = Surveys.index(cur_surv)
                    labels[reg_idx][surv_idx] = ''
                    
        elif self.datatype == 'Observed':
            valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == self.year and self.obs_df['Survey'][r] in Surveys]
            for idx in valid_idx:
                cur_region = self.obs_df['lfs_region'][idx]
                reg_idx = regions.index(cur_region)
                cur_surv = self.obs_df['Survey'][idx]
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
                fish_counts = self.countAllFishSizes(i)
            else:
                fish_counts = self.countSomeFishSizes(i, size_range)
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
#         valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['Survey'][r] in Surveys]
        
        coh_count = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        coh_vol = np.zeros((len(self.poly_names), len(Surveys)),np.float64)
        coh_density = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        coh_abundance = np.zeros((len(self.poly_names),len(Surveys)),np.float64)
        coh_dates = np.zeros((len(self.poly_names),len(Surveys)),dtype=object)
        coh_sizes = np.zeros((len(self.poly_names),len(Surveys)),dtype=object)
        
        orig_size_range = size_range[:]
        #deal with dates and sizes first
        for reg_idx, region in enumerate(self.poly_names):
            in_reg_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['lfs_region'][r] == region and self.obs_df['Survey'][r] in Surveys]
            size_range = orig_size_range[:]
            for surv_idx, surv in enumerate(Surveys): #go through prescribed surveys
                in_surv_idx = [r for r in in_reg_idx if self.obs_df['Survey'][r] == surv] #get each index in prev list where survey is current survey
                for idx in in_surv_idx:
                    cur_date = dt.strptime(self.obs_df['SampleDate'][idx], '%m/%d/%Y 0:00')
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
                        if last_date != np.nan:
                            time_elapsed = coh_dates[reg_idx][surv_idx][0] - last_date
                            growth = time_elapsed.days * 0.14
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
                        fish_counts = self.countAllFishSizes(idx)
                    else:
                        fish_counts = self.countSomeFishSizes(idx, coh_sizes[reg_idx][surv_idx])    
                         
                    coh_count[reg_idx][surv_idx] += fish_counts
                    coh_vol[reg_idx][surv_idx] += cur_vol   
                     
        with open('Cohort_data_{0}_output_{1}.csv'.format(self.runtype.upper(), year), 'wb') as outtext:    
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
    
    def countAllFishSizes(self, index):
        '''add fish at each mm size to one total
        '''
        size_readings = [r for r in self.obs_df.keys() if 'mm' in r]
        total = 0
        for size in size_readings:
            total += self.obs_df[size][index]
        return total
    
    def countSomeFishSizes(self, index, size_range):
        '''add fish at specified mm sizes to one total
        '''
        total = 0
        min = size_range[0]
        max = size_range[1]
        for size in range(min, max+1):
            key = str(size) + 'mm'
            if key in self.obs_df.columns.values:
                total += self.obs_df[key][index]
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
            
        elif plotType == 'Bar':
            maxes = []
            for region in data:
                maxes.append(max(region))
            largest_max = max(maxes)
            len_max = (len(str(largest_max).split('.')[0]) - 2) * -1
            scaler = round(largest_max, len_max)

            
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
                    fish_counts = self.countAllFishSizes(v_idx)
                else:
                    fish_counts = self.countSomeFishSizes(v_idx, size_range)
                cur_survey = self.obs_df['Survey'].values[v_idx]
                survey_idx = yearly_surveys.index(cur_survey)
                obs_count[reg_idx][survey_idx] += fish_counts
                obs_vol[reg_idx][survey_idx] += self.obs_df['Volume'].values[i]
                obs_density[reg_idx][survey_idx] += fish_counts / self.obs_df['Volume'].values[i]
#                 print cur_survey, reg, fish_counts
                reg_abundance[reg_idx][survey_idx] += obs_density[reg_idx][survey_idx] * region_vol
        return reg_abundance
    
    def get_precalc_BW_data(self, surveys):
        '''
        reads in calculated trawl file and organizes it into arrays for Box whisker plots
        Also writes out csv file for easy stat reading
        '''

        region_stats = np.zeros((len(self.poly_names), len(surveys)),dtype=object)
        stats = []

        for region in self.poly_names:
#             print region
            reg_idx = [r for r, reg in enumerate(self.obs_BW_file['region'].values) if reg == region.replace('_', ' ') and self.obs_BW_file['survey'].values[r] in surveys]

            for idx in reg_idx:
                cur_reg = self.obs_BW_file['region'].values[idx].replace(' ', '_')
                reg_idx = self.poly_names.index(cur_reg)
                cur_surv = self.obs_BW_file['survey'].values[idx]
                surv_idx = surveys.index(cur_surv)
                
                item = {}
                item["med"] = self.obs_BW_file['q50'].values[idx]
                item["q1"] = self.obs_BW_file['q25'].values[idx]
                item["q3"] = self.obs_BW_file['q75'].values[idx]
                item["whislo"] = self.obs_BW_file['q5'].values[idx]
                item["whishi"] = self.obs_BW_file['q95'].values[idx]
                region_stats[reg_idx][surv_idx] = item
        return region_stats
        self.write_Box_Stats(region_stats, 'BoxWhisker_Stats_{0}.csv'.format(self.year))
        
    
    def write_Box_Stats(self, stats, filename):
        with open(filename, 'wb') as g:
            g.write('region,survey,q5,q25,q50,q75,q95\n')
            for i, reg in enumerate(self.poly_names):
                for s, surv in enumerate(stats[i]):
                    g.write('{0},{1},{2},{3},{4},{5},{6}\n'.format(reg, s+1, surv['whislo'], surv['q1'], surv['med'], surv['q3'], surv['whishi']))
    
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
            labels = self.findNoData(Surveys) #find correct labels for surveys with no data
            leg_args['max'] = self.get_Plot_Scale(obs_data, 'Bar')
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
                        'bars':boxes,
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
            
            obs_data = self.get_precalc_BW_data(Surveys)
            barxy = self.findSiteLoc(self.poly_names)
            labels = self.findNoData(Surveys)
            
            if leg_args['ylabel'] == 'Density':
                obs_data = self.Abundance_to_Density(obs_data, size_range) #convert abundance data to density
                
            leg_args['max'] = self.get_Plot_Scale(obs_data, 'BoxWhisker')
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
                plt.title('Longfin Smelt Survey {0} {1}mm to {2}mm {3} Cohort {4} {5} '.format(Surveys[0], size_range[0], size_range[1], self.runtype.upper(), plot_type, self.year))
                
            
#             plt.title('Observed {0} {1}'.format(leg_args['ylabel'], self.year))
            
            
            # read observed counts
            coh_data = self.get_Cohort_Data(self.year, Surveys, size_range)
            
            if leg_args['ylabel'] == 'Density':
                coh_data = self.Abundance_to_Density(coh_data, size_range) #convert abundance data to density
            
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            labels = self.findNoData(Surveys) #find correct labels for surveys with no data
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'Bar')
            Longfin_Plot_Utils.plot_bars(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
            new_figname = '_'.join([figname, self.runtype.upper(), str(self.year), str(leg_args['ylabel']), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
            plt.savefig(new_figname, dpi=900, facecolor='white',bbox_inches='tight')
    
            plt.close()
            plt.clf()

        return
    
    def make_MultiCohort_Plot(self, longfile_path1, longfile_path2, figname, size_range, Surveys,static_volumes_file):
        '''UNDER CONSTRUCTION
        Create a plot for cohort growth. cohort growth shows a gradual increase of .14 * days between surveys
        this growth is added to the size range, progressively growing as time goes on.
        includes 2 data sources
        '''
        self.check_runtype()
        self.datatype = 'Observed' #set this parameter for run specific functions
        self.obs_df1 = pd.read_csv(longfile_path1, parse_dates=True)
        self.obs_df2 = pd.read_csv(longfile_path2, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes_file, parse_dates=True)
        
        bars = []
        for num in Surveys:
            bars.append(self.runtype1, '{0}'.format(num))
        for num in Surveys:
            bars.append(self.runtype2, '{0}'.format(num))
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
                plt.title('Longfin Smelt Survey {0} {1}mm to {2}mm {3} Cohort {4} {5} '.format(Surveys[0], size_range[0], size_range[1], self.runtype.upper(), plot_type, self.year))
                
            
#             plt.title('Observed {0} {1}'.format(leg_args['ylabel'], self.year))
            
            
            # read observed counts
            self.obs_df =  self.obs_df1 #set this just for temp reasons
            coh_data1 = self.get_Cohort_Data(self.year, Surveys, size_range)
            self.obs_df =  self.obs_df2 #set this just for temp reasons
            coh_data2 = self.get_Cohort_Data(self.year, Surveys, size_range)
#             coh_data = np.append(coh_data1, coh_data2) #combine the data
            
            if leg_args['ylabel'] == 'Density':
                coh_data1 = self.Abundance_to_Density(coh_data1, size_range) #convert abundance data to density
                coh_data2 = self.Abundance_to_Density(coh_data2, size_range) #convert abundance data to density
            
            barxy = self.findSiteLoc(self.poly_names) #get xy for each site
            labels = self.findNoData(Surveys) #find correct labels for surveys with no data
            leg_args['max'] = self.get_Plot_Scale(coh_data, 'Bar')
            Longfin_Plot_Utils.plot_bars(ax, fig, coh_data, barxy, barboxsize, self.xylims,
                                 leg_args, frac=False, labels=labels)
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
    multicohort = True

    year = 2013 #keep to one year for now, multiyear support coming
    size_range = [6, 8] #inclusive range for the mm values. so min and max values are included in totals
    surveys = [3,4,5,6]

    run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
    grd_file = os.path.join(run_dir, 'ptm.grd')
    cbm = LongfinMaps(run_dir, grd_file, year)
#     bm_inputs = cbm.get_inputs()
    fig_dir = '.'
    
    runtype = 'SLS' #sls or 20mm supported. Changes in Density calcs and titles
    
    if obs_bar:
        figname = os.path.join(fig_dir, 'obs_Bar_Plots')
        obs_data = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.runtype = runtype
        cbm.make_Obs_Barplot(obs_data, figname, size_range, surveys, static_volumes)
    if obs_boxwhisker:
        figname = os.path.join(fig_dir, 'obs_Box_Whisker')
        obs_data = r"J:\Longfin\bar_plots\SLS_quantiles_12mm-25mm_2012.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.runtype = runtype
        cbm.make_precalc_BoxWhiskerPlot(obs_data, figname, size_range, surveys, static_volumes)
    if cohort:
        figname = os.path.join(fig_dir, 'Cohort_Plots')
        obs_data = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.runtype = runtype
        cbm.make_Cohort_Plot(obs_data, figname, size_range, surveys, static_volumes)
    if multicohort:
        figname = os.path.join(fig_dir, 'MultiCohort_Plots')
        obs_data1 = r"J:\Longfin\bar_plots\SLS_trawl_summary.csv"
        obs_data2 = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        cbm.runtype1 = 'SLS'
        cbm.runtype2 = '20mm'
        cbm.make_MultiCohort_Plot(obs_data1, obs_data2, figname, size_range, surveys, static_volumes)


