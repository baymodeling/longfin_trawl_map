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
from datetime import datetime as dtime

max_ab = 10000000 # 10 million

# to do
# - generalize to incorporate data from multiple surveys
# - add "ocean" region to ptm
# - add "landward" region to ptm

utm_dict = {'Central_Delta_and_Franks_Tract':[619700,4208000],
            'Upper_Sacramento_River':[628000,4242000],
            'North_and_South_Forks_Mokelumne_River':[635000,4218000],
            'South_Delta':[635500,4195000],
            'Cache_Slough_Complex':[612000,4245000],
            'Confluence':[609000,4212000],
            'Suisun_Bay':[587000,4216900],
            'Carquinez_Strait':[570500,4208000], 
            'Suisun_Marsh':[588090,4227500],
            'San_Pablo_Bay':[555000,4206700],
            'Petaluma':[538500,4220000],
            'South_SF_Bay':[567000,4164000],
            'Central_SF_Bay':[549500,4190000], 
            'Lower_South_SF_Bay':[586000,4144000], 
            'Napa_Sonoma':[555000,4223500]}

class LongfinBarMaps(object):

    def __init__(self,
                 run_dir,
                 grd_file):
        self.run_dir = run_dir
        self.grd_file = grd_file

    def get_inputs(self):
        # inputs used across all CAMT cases
        self.xylims = [530000,661500,4138000,4295000]
        shp = r"C:\git\longfin_trawl_map\Longfin_hatching_regions.shp"
        dict_field_name = 'Region'
#         shp_e = r'T:\RMA\Projects\CAMT\Analysis\GIS\CVP_and_SWP_regions.shp'
        abundance_file_20mm = r"J:\Longfin\bar_plots\20mm_trawl_summary.csv"
        inpfile = 'FISH_PTM.inp'

        skip_regions=[]

        self.FRAC_FLAG = True
        
        # read 20mm flat file
        self.obs_df = pd.read_csv(abundance_file_20mm, parse_dates=True)

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
                sl = utm_dict[long_name]
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

    def plot_map_obs(self, years, figname, normalize=False):

        fig, ax = self.draw_water_and_polys()
        
        barboxsize = [10000.,10000.]
        leg_args = {'ylabel':'Abundance',
                    'bars':['January','February','March'],
                    'max':max_ab}
        # read observed counts
        obs_data, obs_polys = self.get_obs_data(years, leg_args['bars'])
#         barxy = self.getFishPerRegion(obs_polys)
        barxy = self.findSiteLoc(obs_polys)



        map_w_bars.plot_bars(ax, fig, obs_data, barxy, barboxsize, self.xylims,
                             leg_args, frac=False)

        plt.savefig(figname, dpi=900, facecolor='white', 
                    bbox_inches='tight')
        plt.close()
        plt.clf()

        return

    def get_obs_data(self, years, months):
        
        
        valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date in years]
        obs_polys = self.obs_df['lfs_region'].values[valid_idx]
        obs_poly_box = []
        for polygon in obs_polys:
            if polygon not in obs_poly_box:
                obs_poly_box.append(polygon) 
        obs_data = np.zeros((len(obs_poly_box),len(months)),np.float64)
        
        for i in valid_idx:
            cur_month = self.obs_df['Month'].values[i]
            cur_month = dt.datetime.strptime(str(cur_month), '%m').strftime('%B')
            if cur_month in months:
                cur_region = self.obs_df['lfs_region'].values[i]
                poly_idx = obs_poly_box.index(cur_region)
                fish_counts = self.countAllFishDepths(i)
#                 fish_counts = self.countEachFishDepths(i) #return values at each depth for stacked bars
                month_idx = months.index(cur_month)
                obs_data[poly_idx][month_idx] += fish_counts
        

        return obs_data, obs_polys
    
    def countAllFishDepths(self, index):
        '''add fish at each mm depth to one total
        '''
        depth_readings = [r for r in self.obs_df.keys() if 'mm' in r]
        total = 0
        for depth in depth_readings:
            total += self.obs_df[depth][index]
        return total
    
    def plot_map_obs_size(self, years, figname, normalize=False):

        fig, ax = self.draw_water_and_polys()
        
        barboxsize = [10000.,10000.]
        leg_args = {'ylabel':'Abundance',
                    'bars':['January','February','March'],
                    'max':max_ab}
        
        size_bins = [3, 5, 10, 20, 50, 100] #pick sizes to be put into, first number is 0-#, last number with be #-inf
        # read observed counts
        obs_data, obs_polys = self.get_obs_size_data(years, leg_args['bars'], size_bins)

        barxy = self.findSiteLoc(obs_polys)



        map_w_bars.plot_bars(ax, fig, obs_data, barxy, barboxsize, self.xylims,
                             leg_args, frac=False)

        plt.savefig(figname, dpi=900, facecolor='white', 
                    bbox_inches='tight')
        plt.close()
        plt.clf()

        return     
    
    def get_obs_size_data(self, years, months, size_bins):
        
        num_size_bins = len(size_bins) + 1
        
        valid_idx = [r for r, date in enumerate(self.obs_df['Year'].values) if date in years]
        obs_polys = self.obs_df['lfs_region'].values[valid_idx]
        obs_poly_box = []
        for polygon in obs_polys:
            if polygon not in obs_poly_box:
                obs_poly_box.append(polygon) 
        obs_data = np.zeros((len(obs_poly_box),len(months), num_size_bins),np.float64)
        
        for i in valid_idx:
            cur_month = self.obs_df['Month'].values[i]
            cur_month = dt.datetime.strptime(str(cur_month), '%m').strftime('%B')
            if cur_month in months:
                cur_region = self.obs_df['lfs_region'].values[i]
                poly_idx = obs_poly_box.index(cur_region)
                fish_counts = self.countEachFishDepths(i, size_bins)
#                 fish_counts = self.countEachFishDepths(i) #return values at each depth for stacked bars
                month_idx = months.index(cur_month)
                obs_data[poly_idx][month_idx] += fish_counts
                
        return obs_data, obs_polys    
            
    def countEachFishDepths(self, index, size_bins):
        '''return fish depth at each mm depth
        '''
        depth_readings = [r for r in self.obs_df.keys() if 'mm' in r]
        sizes = np.zeros(len(size_bins) + 1)
        for depth in depth_readings:
            depnum = int(depth.split('mm')[0])
            last_idx = 0
            for bin in size_bins:
                if depnum >= size_bins[-1]: #just check if its bigger than the biggest bin...
                    last_idx = len(sizes)
                    break
                elif depnum < bin:
                    break
                else:
                    last_idx += 1
            sizes[last_idx] += self.obs_df[depth][index]
        
        #TODO this
    
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
        gcoll = self.grd.plot_cells(mask=self.g_mask, facecolor=blu, 
                                    edgecolor=blu)

        # plot relevant polygons
        polys_from_shp.plot_polygons(self.plot_poly_dict,color='k')

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
            barxy[s] = utm_dict[site]
        
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
    test_pred = False
    test_obs = True
    test_obs_vs_pred = False
    test_metrics = False

    run_dir = r'Z:\PTM_Simulations\Longfin\2012_all_behaviors\Run'
    grd_file = os.path.join(run_dir, 'FISH_PTM.grd')
    cbm = LongfinBarMaps(run_dir, grd_file)
    bm_inputs = cbm.get_inputs()
    fig_dir = '.'
    years = [2012]
    if test_obs:
        figname = os.path.join(fig_dir, 'obs_monthly.png')
        cbm.plot_map_obs(years, figname)
        figname = os.path.join(fig_dir, 'obs_size.png')
        cbm.plot_map_obs_size(years, figname)
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


