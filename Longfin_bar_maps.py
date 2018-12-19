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
# import camt_region_dicts
from stompy.grid import unstructured_grid
from rmapy.utils.gis import polygons_w_attributes_from_shp as polys_from_shp
import fish_ptm_results
import map_w_bars
import map_w_boxes
from datetime import datetime as dtime


# to do
# - generalize to incorporate data from multiple surveys
# - add "ocean" region to ptm
# - add "landward" region to ptm


class LongfinBarMaps(object):

    def __init__(self,
                 run_dir,
                 grd_file,
                 year):
        self.run_dir = run_dir
        self.grd_file = grd_file
        self.year = year

    def get_inputs(self):
        # inputs used across all CAMT cases
        self.xylims = [530000,661500,4138000,4295000]
        shp = r"C:\git\longfin_trawl_map\Longfin_hatching_regions.shp"
        dict_field_name = 'Region'
#         shp_e = r'T:\RMA\Projects\CAMT\Analysis\GIS\CVP_and_SWP_regions.shp'
#         abundance_file_20mm = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        inpfile = 'FISH_PTM.inp'
        static_volumes = r"C:\git\longfin_trawl_map\static_volumes_1.25m_NAVD.csv"
        
#         BW_data_file = r"J:\Longfin\bar_plots\20mm_quantiles_{0}.csv".format(self.year)
        skip_regions=[]
        
        self.FRAC_FLAG = True
        
        # read 20mm flat file
#         self.obs_df = pd.read_csv(abundance_file_20mm, parse_dates=True)
        self.obs_static_vol = pd.read_csv(static_volumes, parse_dates=True)
#         self.obs_BW_file = pd.read_csv(BW_data_file, parse_dates=True)
        self.inpfile = os.path.join(self.run_dir,inpfile)
        
#         crd = camt_region_dicts.CamtRegionDicts(shp, shp_e, self.inpfile) #camt shapefile
#         self.region_dicts = crd.get_region_dicts() #cmat regions. Unneeded?

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
        
    def plot_map_pred(self, model, year, gname, figname):

        fig, ax = self.draw_water_and_polys()

        survey_dates = self.get_survey_dates(year)
        nsurveys = len(survey_dates)
        pred_data, count_polys = self.get_pred(gname, model, survey_dates)
        barxy = self.findSiteLoc(count_polys)

        barboxsize = [10000.,10000.]
        leg_args = {'ylabel':'Fraction',
                    'bars':['January','February','March'],
                    'max':max_ab}

        map_w_bars.plot_bars(ax, fig, pred_data, barxy, barboxsize, self.xylims,
                             leg_args, frac=True)

        plt.savefig(figname, dpi=900, facecolor='white', 
                    bbox_inches='tight')
        plt.close()
        plt.clf()

        return

    def plot_map_pred_fish(self, model, year, rtime, fitdir, movdir, gname, 
                           figname):

        fig, ax = self.draw_water_and_polys()

        survey_dates = self.get_survey_dates(year)
        nsurveys = len(survey_dates)
        self.set_fate_to_number(movdir, gname, rtime) # fairly hardwired method
        pred_data = self.get_pred_fish(fitdir, gname, rtime, survey_dates)
        barxy = self.findSiteLoc(self.fates)

        barboxsize = [10000.,10000.]
        leg_args = {'ylabel':'Abundance',
                    'bars':['January','February','March'],
                    'max':max_ab}

        map_w_bars.plot_bars(ax, fig, pred_data, barxy, barboxsize, self.xylims,
                             leg_args, frac=False)
        plt.savefig(figname, dpi=900, facecolor='white', 
                    bbox_inches='tight')
        plt.close()
        plt.clf()

        return

    def plot_map_obs_pred_fish(self, obs_file, model, year, rtime, fitdir, 
                               movdir, gname, figname):

        reg_ab = fit_results.load_obs_regional_abundance(obs_file)

        fig, ax = self.draw_water_and_polys()

        survey_dates = self.get_survey_dates(year)
        nsurveys = len(survey_dates)
        self.set_fate_to_number(movdir, gname, rtime) # fairly hardwired method
        pred_data = self.get_pred_fish(fitdir, gname, rtime, survey_dates)
        bardata = np.zeros((len(pred_data),nsurveys*2),np.float64)
        #bardata = np.ones((len(pred_data),nsurveys*2),np.float64)*np.nan
        for nsur in range(nsurveys):
            bardata[:,nsur*2+1] = pred_data[:,nsur]
            for nreg, pred in enumerate(pred_data):
                if nreg < len(reg_ab): # can't set obs seaward loss or entrain
                    bardata[nreg,nsur*2] = reg_ab[nreg,nsur]
#       for nreg, pred in enumerate(pred_data):
#           bardata[nreg*2,:] = pred_data[nreg,:]
#           if nreg < len(reg_ab): # can't set observed seaward loss or entrain
#               bardata[nreg*2+1,:] = reg_ab[nreg,:]
        barxy = self.findSiteLoc(self.fates)

        barboxsize = [10000.,10000.]
        barboxsize = [10000.,8000.]
        leg_args = {'ylabel':'Abundance',
                    'bars':['January','February','March'],
                    'max':max_ab}

        map_w_bars.plot_bars(ax, fig, bardata, barxy, barboxsize, self.xylims,
                             leg_args, frac=False, alt_hatch=True)
        # x out losses and entrain for obs (15 and 16)?

        plt.savefig(figname, dpi=900, facecolor='white', 
                    bbox_inches='tight')
        plt.close()
        plt.clf()

        return
        
    # need group name to line up region numbers using movement table
    def plot_map_obs_fish(self, obs_file, year, movdir, gname, rtime, figname):

        reg_ab = fit_results.load_obs_regional_abundance(obs_file)
        nreg = len(reg_ab)

        fig, ax = self.draw_water_and_polys()

        survey_dates = self.get_survey_dates(year)
        nsurveys = len(survey_dates)
        self.set_fate_to_number(movdir, gname, rtime) # fairly hardwired method
        barxy = self.findSiteLoc(self.fates[:nreg])

        barboxsize = [10000.,10000.]
        barboxsize = [10000.,8000.]
        leg_args = {'ylabel':'Abundance',
                    'bars':['January','February','March'],
                    'max':max_ab}

        map_w_bars.plot_bars(ax, fig, reg_ab, barxy, barboxsize, self.xylims,
                             leg_args, frac=False, alt_hatch=False)
        # x out losses and entrain for obs (15 and 16)?

        plt.savefig(figname, dpi=900, facecolor='white', 
                    bbox_inches='tight')

        plt.close()
        plt.clf()

        return

    def set_fate_to_number(self, movdir, gname, rtime=dtime(2001,12,5)):
        short_to_long = self.region_dicts['short_to_long']

        # read movement table csv file
        gname = gname.replace('_Sac','')
        rdate = pylab.num2date(rtime)
        dstamp = rdate.strftime('%b%#d_%Y')
#       dstamp = '{dt.%b}{dt.day}_{dt.year}'.format(dt)
        move_file = os.path.join(movdir,gname+'_'+dstamp+'.csv')
        mf_dict = pd.read_csv(move_file)
        all_short_names = mf_dict['to_region']
        short_names_uniq, idx = np.unique(all_short_names, return_index=True)
        short_names_in_mov = short_names_uniq[np.argsort(idx)]
        fate_to_number = {}
        pumps = []
        losses = []
        fate_list = []
        # check if long name is in SiteLoc
        for ns, short_name in enumerate(short_names_in_mov):
            if 'pumps' in short_name:
                pumps.append(ns)
            elif short_name == 'cc':
                continue # ignore cc counts for now
            else:
                long_name = short_to_long[short_name]
                sl = self.utm_dict[long_name]
                if not np.isnan(sl[0]):
                    fate_to_number[long_name]=[ns]
                    fate_list.append(long_name)
                else:
                    losses.append(ns)
        # hardwired categories
        fate_to_number['Entrained'] = pumps
        fate_to_number['Domain_Losses'] = losses
        fate_list.append('Entrained')
        fate_list.append('Domain_Losses')

        self.fate_to_number = fate_to_number
        self.fates = fate_list

        return 

    # single month plot obs vs. pred
    def plot_map_obs_pred(self, year, month, scenarios, labels, figname):

        fig, ax = self.draw_water_and_polys()

        ngroups = len(labels)
            
        # get bardata (fraction in each region) for survey periods
        survey_dates = self.get_survey_dates(year)

        pred_data = {}
        for label in labels:
            scenario = scenarios[label]
            # read predicted counts
            gname = scenario['group_name']
            rdir  = scenario['run_dir']
            model = scenario['model']
            pred_data[label], count_polys = self.get_pred(gname, 
                model, survey_dates, rdir = rdir)
        barxy = self.findSiteLoc(count_polys)

        obs_data, obs_polys = self.get_obs_data(year)

        # reorder obs_data to match order of count_polys
        obs_data_frac = np.zeros_like(pred_data[labels[0]])
        obs_total = np.sum(obs_data,axis=0)
        for npol, poly in enumerate(obs_polys):
            n = count_polys.index(poly)
            obs_data_frac[n,:] = np.divide(obs_data[npol,:],obs_total)
          
        survey = month_to_survey[month]
        bardata = np.zeros((len(count_polys),ngroups+1),np.float64)
        # first bar is observed counts
        bardata[:,0] = obs_data_frac[:,survey]
        for nl, label in enumerate(labels):
            bardata[:,nl+1] = pred_data[label][:,survey]

        barboxsize = [10000.,10000.]
        leg_args = {'ylabel':'Fraction',
                    'bars':['Observed']+labels,
                    'max':max_ab}
        map_w_bars.plot_bars(ax, fig, bardata, barxy, barboxsize, self.xylims,
                             leg_args, frac=True)

        plt.savefig(figname, dpi=900, facecolor='white', 
                    bbox_inches='tight')
        plt.close()
        plt.clf()

        return

    # output raw and normalized info to csv file
    def compute_metrics(self, model, year, gnames, csv_dir):

        ngroups = len(gnames)
        
        # get bardata (fraction in each region) for survey periods
        survey_dates = self.get_survey_dates(year)
        nsurveys = len(survey_dates)

        pred_data = {}
        raw_data = {}
        for gname in gnames:
            # read predicted counts
            raw_data[gname], pred_data[gname], count_polys = self.get_pred(gname, model, survey_dates, output_raw = True)
        obs_data, obs_polys = self.get_obs_data(year)

        npolys = len(count_polys)
        nobspolys = len(obs_polys)
        # reorder obs_data to match order of count_polys
        map_pred_to_obs = np.zeros(len(obs_polys),np.int32)
        map_obs_to_pred = np.zeros(npolys,np.int32)
        obs_data_reorder = np.zeros((npolys,nsurveys),np.float64)
        for npol, poly in enumerate(obs_polys):
            n = count_polys.index(poly)
            map_pred_to_obs[npol] = n
            map_obs_to_pred[n] = npol
            # can't do by simple mapping because pred is longer than obs
            obs_data_reorder[n] = obs_data[npol]
        obs_tot = np.sum(obs_data,axis=0)
        obs_data_frac = np.divide(obs_data,obs_tot)
        obs_data_r_frac = np.divide(obs_data_reorder,obs_tot)
        polysX3 = [r for r in count_polys for ns in range(nsurveys)]
        obs_polysX3 = [r for r in obs_polys for ns in range(nsurveys)]
        rnumX3 =  [self.region_dicts['nr_dict'][r]+1 for r in obs_polys 
                   for ns in range(nsurveys)]
        shortX3 = [self.region_dicts['rg_dict'][r] for r in obs_polys 
                  for ns in range(nsurveys)]
        months = month_to_survey.keys()
        monthsXpolys = []
        for npol in range(npolys):
            monthsXpolys += [m for m in months]
        obs_monthsXpolys = []
        for npol in range(nobspolys):
            obs_monthsXpolys += [m for m in months]
        # calculate metrics - 'reorder' to only observed regions
        obsr =  np.ravel(obs_data_reorder)
        obs = np.ravel(obs_data)
        obsrn = np.ravel(obs_data_r_frac)
        obsn = np.ravel(obs_data_frac)
        corr = np.zeros(ngroups, np.float64)
        for ng, gname in enumerate(gnames):
            predr_2d = raw_data[gname][map_pred_to_obs]
            predr = np.ravel(predr_2d)
            predrn_2d = pred_data[gname][map_pred_to_obs]
            predrn = np.ravel(predrn_2d)
            m, b, r, p, se = stats.linregress(obsn, predrn)
            corr[ng] = r
            print "gname, r",gname, r
            pred   = np.ravel(raw_data[gname])
            predn = np.ravel(pred_data[gname])
            csv_data = {'region':polysX3,
                        'month':monthsXpolys,
                        'obs':obsr,
                        'pred':pred,
                        'obsn':obsrn,
                        'predn':predn}
            csv_columns = ['region','month','obs','pred','obsn','predn']
            csv_frame = pd.DataFrame(csv_data, columns=csv_columns)
            csv_name = os.path.join(csv_dir, gname+'.csv')
            csv_frame.to_csv(csv_name, index=False)
            csv_data_o = {'region':obs_polysX3,
                          'short':shortX3,
                          'reg_num':rnumX3,
                          'month':obs_monthsXpolys,
                          'obs':obs,
                          'pred':predr,
                          'obsn':obsn,
                          'predn':predrn}
            csv_columns = ['region','short','reg_num','month','obs','pred',
                           'obsn','predn']
            csv_frame = pd.DataFrame(csv_data_o, columns=csv_columns)
            csv_name = os.path.join(csv_dir, gname+'_o.csv')
            csv_frame.to_csv(csv_name, index=False)
        metrics = {'groups':gnames,
                   'corr':corr}
        metric_columns = ['groups','corr']
        metric_frame = pd.DataFrame(metrics, columns=metric_columns)
        metric_frame.to_csv('metrics.csv',index=False)

        return

    def get_pred_fish(self, fitdir, gname, rtime, survey_dates):
        fitr = fit_results.FitResults(gname, self.region_dicts, rtime, fitdir)
        pred_entrain = fitr.load_entrain()
        pred_counts = fitr.load_region_counts()
        # add 0.5 to make it noon
        dnums = [rtime + nday + 0.5 for nday in range(len(pred_entrain))]
        all_dates = np.array(pylab.num2date(dnums), dtype='datetime64[us]')
#       hardwired. Assume 15 regions then combine other into domain_losses
        npolys = 15
        nfates = len(self.fates)
        ncounts = len(pred_counts[0])
        ndays = len(dnums)
        pred_ts= np.zeros((nfates,ndays),np.float64)
        for npol in range(npolys):
            pred_ts[npol,:] = pred_counts[:,npol]
        # domain losses
        for npol in range(npolys,ncounts):
            pred_ts[npolys+1,:] += pred_counts[:,npol]
        # entrainment
        pred_ts[npolys,:] = np.cumsum(pred_entrain)

        pred_data = np.zeros(shape=(nfates,len(survey_dates)))
        nsurveys = len(survey_dates)
        for ns, sdates in enumerate(survey_dates):
            rows = np.intersect1d(np.where(all_dates>=sdates[0]),
                                  np.where(all_dates<=sdates[1]))
            for nreg, region in enumerate(self.fates):
                pred_data[nreg,ns] = np.average(pred_ts[nreg,rows])
                # don't double count the two added categores (Domain and Entrained)
        return pred_data

    def get_pred(self, gname, model, survey_dates, rdir=None, output_raw=False):
        if model == 'FISH-PTM':
            if rdir == None:
                rdir = self.run_dir
            ptmr = fish_ptm_results.PtmResults(gname, self.region_dicts, 
                                               self.inpfile, rdir)
        else:
            print "model not implemented"
            return

        if output_raw == False:
            pred_data, count_polys = self.readData_predict(ptmr, survey_dates,
                                                           output_raw=False)
            return pred_data, count_polys
        else:
            raw_data, pred_data, count_polys = self.readData_predict(ptmr, 
                                               survey_dates, output_raw=True)
            return raw_data, pred_data, count_polys

    def findNoBarData(self, Surveys, year):
        regions = self.poly_names
        labels = np.chararray((len(regions), len(Surveys)))
        labels[:] = 'X'
        valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date == year and self.obs_df['Survey'][r] in Surveys]
        for idx in valid_idx:
            cur_region = self.obs_df['lfs_region'][idx]
            reg_idx = regions.index(cur_region)
            cur_surv = self.obs_df['Survey'][idx]
            bar_idx = Surveys.index(cur_surv)
            labels[reg_idx][bar_idx] = ''

        return labels
    
    def findNoBoxData(self, Surveys):
        regions = self.poly_names
        labels = np.chararray((len(regions), len(Surveys)))
        labels[:] = 'X'
        valid_idx = [r for r, survey in enumerate(self.obs_BW_file['survey'].values) if survey in Surveys]
        for idx in valid_idx:
            if not np.isnan(self.obs_BW_file['q5'].values[idx]):
                cur_region = self.obs_BW_file['region'][idx].replace(' ', '_')
                reg_idx = regions.index(cur_region)
                cur_surv = self.obs_BW_file['survey'][idx]
                surv_idx = Surveys.index(cur_surv)
                labels[reg_idx][surv_idx] = ''

        return labels

    def plot_map_obs(self, longfile_path, figname, size_range, Surveys, normalize=False):
        '''
        Creates a bar plot of the Abundance for a particular year.
         many surveys is untested and may look really ugly. Consider keeping 9 surveys max.
        
        '''
        self.obs_df = pd.read_csv(longfile_path, parse_dates=True)

        fig, ax = self.draw_water_and_polys()
        bars = []
        for num in Surveys:
            bars.append('Survey {0}'.format(num))
        barboxsize = [10000.,10000.] #determines size of plots. Don't touch.
        leg_args = {'ylabel':'Density',
                    'bars':bars,
                    'max':''}
        
        if leg_args['ylabel'] == 'Density':
            leg_args['max'] = self.max_den[self.year]
        elif leg_args['ylabel'] == 'Abundance':
            leg_args['max'] = self.max_ab[self.year]
            
        plt.title('Observed {0} {1}'.format(leg_args['ylabel'], self.year))
        
        
        # read observed counts
        obs_data = self.get_obs_data(self.year, Surveys, size_range)
        
        if leg_args['ylabel'] == 'Density':
            obs_data = self.Abun_to_Density_Bar(obs_data) #convert abundance data to density
        
        barxy = self.findSiteLoc(self.poly_names) #get xy for each site
        labels = self.findNoBarData(Surveys, self.year) #find correct labels for surveys with no data
        map_w_bars.plot_bars(ax, fig, obs_data, barxy, barboxsize, self.xylims,
                             leg_args, frac=False, labels=labels)
        figname = '_'.join([figname, str(self.year), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
        plt.savefig(figname, dpi=900, facecolor='white',bbox_inches='tight')

        plt.close()
        plt.clf()

        return

    def get_obs_data(self, year, Surveys, size_range):
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
            outtext.write('region,year,survey,fish count,volume per Survey,Density in 10000 fish per m3,Region Volume,Reg Abundance\n')
            for i, region in enumerate(self.poly_names):
#                 print region
                vol_file_idx = np.where(self.obs_static_vol['region_name'].values == region.replace('_',' '))[0][0]
                region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
                for j, survey_cnt in enumerate(obs_count[i]):
#                     print survey_cnt
                    obs_density[i][j] = survey_cnt / obs_vol[i][j] 
                    reg_abundance[i][j] = obs_density[i][j] * region_vol
                    reg_abundance = np.nan_to_num(reg_abundance)
                    outline = ','.join([str(r) for r in [region, year, j+1, survey_cnt, obs_vol[i][j], obs_density[i][j] * 10000, region_vol, reg_abundance[i][j], '\n']])
                    outtext.write(outline)
        
        return reg_abundance
    
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
    
    def Abun_to_Density_BW(self, obs_Data, size_range):
        '''
        Converts Abundance to density (fish per 10,000 m3)
        Currently only applies to Boxwhisker plots, for when Density is selected
        also writes out a csv file for density stats 
        '''
        obs_density = np.empty_like(obs_Data)
        for i, reg in enumerate(self.poly_names):
            vol_file_idx = np.where(self.obs_static_vol['region_name'].values == reg.replace('_',' '))[0][0]
            region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
            for s, surv in enumerate(obs_Data[i]):
                obs_density[i][s] = {}
                for key in surv.keys():
                    obs_density[i][s][key] = (surv[key] / region_vol) * 10000.
#                 obs_density[i][s] = surv / region_vol * 10000 #get density by dividing region vol and then 100000 fishies
        self.write_Box_Stats(obs_density, 'Density_BoxWhisker_Stats_{0}_{1}mm-{2}mm.csv'.format(self.year, size_range[0], size_range[1]))
                
        return obs_density
    
    def Abun_to_Density_Bar(self, obs_Data):
        '''
        Converts Abundance to density (fish per 10,000 m3)
        Currently only applies to Bar plots, for when Density is selected
        Does not write a csv like the other file since density is in the first
        '''
        obs_density = np.empty_like(obs_Data)
        for i, reg in enumerate(self.poly_names):
            vol_file_idx = np.where(self.obs_static_vol['region_name'].values == reg.replace('_',' '))[0][0]
            region_vol = self.obs_static_vol['vol_top_999_m'][vol_file_idx]
            for s, surv in enumerate(obs_Data[i]):
                obs_density[i][s] = (surv / region_vol) * 10000.
                
        return obs_density
            
            
            
    def plot_obs_boxwhisker(self, data_path, figname, size_range, Surveys):
        '''
        Plots Box Whisker plots for observed data in trawl files
        data is precalculated and does NOT come from long file, but is possible
        ylabel can be set to "Abundance" or "Density"
        '''
        self.obs_BW_file = pd.read_csv(data_path, parse_dates=True)
        fig, ax = self.draw_water_and_polys()
        boxes = []
        
        for num in Surveys:
            boxes.append('Survey {0}'.format(num))

        leg_args = {'ylabel':'Abundance',
                    'boxes':boxes,
                    'max':''}
        
        if leg_args['ylabel'] == 'Density':
            leg_args['max'] = self.max_den[self.year]
        elif leg_args['ylabel'] == 'Abundance':
            leg_args['max'] = self.max_ab[self.year]

        
        plt.title('Observed {0} {1}'.format(leg_args['ylabel'], self.year))
        barboxsize = [10000.,10000.]
        
        obs_data = self.get_precalc_BW_data(Surveys)
        barxy = self.findSiteLoc(self.poly_names)
        labels = self.findNoBoxData(Surveys)
        
        if leg_args['ylabel'] == 'Density':
            obs_data = self.Abun_to_Density_BW(obs_data, size_range) #convert abundance data to density
        map_w_boxes.plot_boxes(ax, fig, obs_data, barxy, barboxsize, self.xylims,
                             leg_args, frac=False, labels=labels)

        figname = '_'.join([figname, str(self.year), '{0}mm-{1}mm.png'.format(size_range[0], size_range[1])])
        plt.savefig(figname, dpi=900, facecolor='white',
                    bbox_inches='tight')

        plt.close()
        plt.clf()

        return
    
    
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
        self.write_Box_Stats(region_stats, 'BoxWhisker_Stats_{0}.csv'.format(self.year))
        return region_stats
    
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
        
    def write_Box_Stats(self, stats, filename):
        with open(filename, 'wb') as g:
            g.write('region,survey,q5,q25,q50,q75,q95\n')
            for i, reg in enumerate(self.poly_names):
                for s, surv in enumerate(stats[i]):
                    g.write('{0},{1},{2},{3},{4},{5},{6}\n'.format(reg, s+1, surv['whislo'], surv['q1'], surv['med'], surv['q3'], surv['whishi']))
                
        
        
   
            
    
    def get_obs_from_fit(self, year):
        dformat = '%Y-%m-%d'
        rows = np.where(self.obs_df['Yr'].values==year)[0]
        survey_dates = np.empty((len(rows),2),dtype='datetime64[us]')
        short2long = {s: l for l, s in self.region_dicts['rg_dict'].iteritems()}
        obs_polys = [r for r in self.obs_df.keys() if r in short2long.keys()]
        obs_polys_long = [] # long names used in findSiteLoc
        obs_data = np.zeros((len(obs_polys),len(rows)),np.float64)
        for nr, reg in enumerate(obs_polys):
            obs_polys_long.append(short2long[reg])
            obs_data[nr,:] = self.obs_df[reg][rows]

        return obs_data, obs_polys_long
        
    def draw_water_and_polys(self):

        fig = plt.figure(figsize=[10,10])
        ax = fig.add_subplot(111)

        # plot grid in solid blue color
        self.get_grid_masks()
        blu = '#add8e6'
        grey = '#A9A9A9'
        gcoll = self.grd.plot_cells(mask=self.g_mask, facecolor=blu, 
                                    edgecolor=blu)

        # plot relevant polygons
        polys_from_shp.plot_polygons(self.plot_poly_dict,color=grey)

        return fig, ax

    def get_survey_dates(self, year):
        dformat = '%Y-%m-%d'
        rows = np.where(self.obs_df['Yr'].values==year)[0]
        survey_dates = np.empty((len(rows),2),dtype='datetime64[us]')
        for nr, row in enumerate(rows):
            survey_dates[nr,0] = dt.strptime(self.obs_df['start_date'][row],dformat)
            survey_dates[nr,1] = dt.strptime(self.obs_df['end_date'][row],dformat)

        return survey_dates

    def get_grid_masks(self):
        g = self.grd
        centers = g.cells_center(refresh=True)
        self.g_mask = g.cell_clip_mask(self.xylims)
        self.e_mask = g.edge_clip_mask(self.xylims)

        return

    def findSiteLoc(self, site_names):
        # Reads dictionary for easting, northing and returns those coordinates.
        
        barxy = np.zeros((len(site_names),2),np.float64)
        for s,site in enumerate(site_names):
            barxy[s] = self.utm_dict[site]
        
        return barxy

    # should rework this to read the movement table instead
    def readData_predict(self, ptm_results, survey_dates, output_raw = False):

        ptm_results.load_map_data()
        all_dates = np.array(pylab.num2date(ptm_results.dnums_noon),
                             dtype='datetime64[us]')
        
        bar_plots = ptm_results.counts_dict.keys()
        npolys = len(bar_plots)
        nbar_plots = npolys + 2 # 2 hardwired "regions"
        bardata = np.zeros(shape=(nbar_plots,len(survey_dates)))
        surdata = np.zeros(shape=(nbar_plots,len(survey_dates)))
        rawdata = np.zeros(shape=(nbar_plots,len(all_dates)))
        # Average data over appropriate time range according to survey_dates.
        for nreg, region in enumerate(bar_plots):
            rawdata[nreg,:] = ptm_results.counts_dict[region]
        bar_plots.append('Entrained')
        rawdata[npolys,:] = np.cumsum(ptm_results.ecounts)
        ptm_results.counts_dict['Entrained'] = rawdata[npolys,:]
        bar_plots.append('Domain_Losses')
        rawdata[npolys+1,:] = ptm_results.counts_dict['San_Francisco_Bay'] + \
            ptm_results.counts_dict['San_Pablo_Bay'] +\
            ptm_results.counts_dict['South_South_Delta'] +\
            ptm_results.counts_dict['Sacramento_River_North'] +\
            ptm_results.counts_dict['Yolo'] 
        ptm_results.counts_dict['Domain_Losses'] = rawdata[npolys+1,:]
        nsurveys = len(survey_dates)
        total_particles = np.zeros(nsurveys, np.float64)
        for ns, sdates in enumerate(survey_dates):
            rows = np.intersect1d(np.where(all_dates>=sdates[0]),
                                  np.where(all_dates<=sdates[1]))
            for nreg, region in enumerate(bar_plots):
                surdata[nreg,ns] = np.average(rawdata[nreg,rows])
                # don't double count the two added categores (Domain and Entrained)
                if nreg < npolys:
                    total_particles[ns] += surdata[nreg,ns]
        
        if self.FRAC_FLAG:
            for ns, sdates in enumerate(survey_dates):
                bardata[:,ns] = surdata[:,ns]/total_particles[ns]
   
        if output_raw:
            return surdata, bardata, bar_plots
        else:
            return bardata, bar_plots

if __name__ == '__main__':
    # test for single predicted distribution plot
    test_pred = False #Out of Order
    obs_bar = True
    obs_boxwhisker = True
    test_obs_vs_pred = False #Out of Order
    test_metrics = False #Out of Order

    year = 2012 #keep to one year for now, multiyear support coming
    size_range = [12, 25] #inclusive range for the mm values. so min and max values are included in totals
    surveys = [1,2,3,4,5,6,7,8,9]

    run_dir = r'J:\Longfin\bar_plots\FISH_PTM'
    grd_file = os.path.join(run_dir, 'ptm.grd')
    cbm = LongfinBarMaps(run_dir, grd_file, year)
    bm_inputs = cbm.get_inputs()
    fig_dir = '.'
    
    if obs_bar:
        figname = os.path.join(fig_dir, 'obs_Bar_Plots')
        obs_data = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        cbm.plot_map_obs(obs_data, figname, size_range, surveys)
    if obs_boxwhisker:
        figname = os.path.join(fig_dir, 'obs_Box_Whisker')
        obs_data = r"J:\Longfin\bar_plots\20mm_quantiles_larvae_{0}.csv".format(year)
#         obs_data = r"J:\Longfin\bar_plots\20mm_quantiles_small_larvae_{0}.csv".format(year)
        cbm.plot_obs_boxwhisker(obs_data, figname, size_range, surveys)
    if test_pred:
        model = 'FISH-PTM'
        gname = 'tmd_Sac'
        figname = os.path.join(fig_dir, gname+'_map.png')
        cbm.plot_map_pred(model, year, gname, figname)
    if test_obs_vs_pred:
        figname = os.path.join(fig_dir, 'tmd_release_date.png')
        model = 'FISH-PTM'
        Dec5_dir = 'F:\PTM_simulations\CAMT\Dec5_2001_sac_bw\Run'
        Dec20_dir = '..\Run'
        scenarios = {}
        scenarios['Dec 5'] = {'model':model,
                              'group_name':'tmd_Sac',
                              'run_dir':Dec5_dir}
        scenarios['Dec 20'] = {'model':model,
                               'group_name':'tmd_Sac',
                               'run_dir':Dec20_dir}
        labels = ['Dec 5','Dec 20']
        month = 'January'
        cbm.plot_map_obs_pred(year, month, scenarios, labels, figname)
    if test_metrics:
        csv_dir = r'.\csv'
        gnames = ['passive_Sac','tmd_Sac','ptmd_sal_gt_1_si_pt_5_Sac']
        model = 'FISH-PTM'
        cbm.compute_metrics(model, year, gnames, csv_dir)


