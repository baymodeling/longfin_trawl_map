# note this code assumes that the distribution and entrainment plotting
# has been performed and the associated .csv files are available
import os, sys
from datetime import datetime
import ptm_time_utils
import ptm_inp_reader
import ptm_counts_reader
import numpy as np
import pdb
import local_utils as utils
gis_lib_path = r'C:\svn\Code\python\rma\gis'
if gis_lib_path not in sys.path:
    sys.path.insert(0,gis_lib_path)

# where should these lists and dictionaries live?
beh_types = ['passive',
             'holding',
             'tmd',
             'rtmd',
             'rheo',
             'psm',
             'turbidity',
             'freshwater']
nbt = len(beh_types)
beh_names = {'passive':'Passive',
             'holding':'Holding',
             'tmd':'Tidal Migration',
             'rtmd':'Reverse Tidal Migration',
             'rheo':'Rheotaxis',
             'psm':'Pre-spawning Migration',
             'turbidity':'Turbidity Seeking',
             'freshwater':'Freshwater Seeking'}

frac_list = ['retained','seaward','entrained']

class PtmResults(object):

    def __init__(self,
                 group_name,
                 region_dicts,
                 inpfile,
                 run_dir):
        self.group_name = group_name
        self.region_dicts = region_dicts
        self.run_dir = run_dir
        self.inpfile = inpfile
        self.base_dir = os.path.split(self.run_dir)[0]

    def load_4panel_data(self):
        # read and filter entrainment counts
        self.ednums, self.ecounts = self.load_entrain_counts()
        # get distribution counts
        self.get_fate_fractions()
        # read and filter behavior counts
        self.bdnums, self.bcounts = self.filtered_behavior_counts()

        return 

    def load_map_data(self):
        # read and filter entrainment counts
        self.ednums, self.ecounts = self.load_entrain_counts()
        self.dnums, self.counts = self.load_counts()
        dt_hours = (self.dnums[1] - self.dnums[0])*24.
        self.counts_dict = {}
        for region in self.region_dicts['nr_dict']:
            nr = self.region_dicts['nr_dict'][region]
            fil_counts = utils.Godin(self.counts[nr], dt_hours)
            dnums_noon, daily_counts = utils.daily_at_noon(self.dnums,
                                                           fil_counts)
            self.counts_dict[region] = daily_counts
        self.dnums_noon = dnums_noon
#       self.counts_dict['Entrained'] = self.ecounts

        return 

    def get_fate_fractions(self):
        dnums, counts = self.load_counts()
        # form and filter aggregate counts
        self.dnums, da = self.filtered_aggregate_counts(dnums,counts)
        self.frac = self.fate_frac(self.dnums, da, self.ednums, self.ecounts)

    def load_counts(self):
        counts_sums={}
        counts_file = os.path.join(self.run_dir,self.group_name+'_avg_region.out')
        pc = ptm_counts_reader.PTMcounts(counts_file)
        inpfile = os.path.join(self.run_dir,self.inpfile)
        pi = ptm_inp_reader.PTMinput(inpfile)
        nregions = len(pi.get_regions())
        dnums = pc.get_dates(nregions)
        ndates = len(dnums)
        data = pc.get_data(nregions,ndates)

        return dnums, data['count']
        
    def filtered_aggregate_counts(self, dnums, counts):
        dt_hours = (dnums[1] - dnums[0])*24.
        agg_regions = self.region_dicts['agg_regions']
        daily_counts = {}
        ar_index_dict = self.region_dicts['ar_index_dict']
        for na, ar in enumerate(agg_regions):
            inds = ar_index_dict[ar]
            agg_counts = np.sum(counts[inds,:],axis=0)
            fil_counts = utils.Godin(agg_counts, dt_hours)
            dnums_noon, daily_counts[ar] = utils.daily_at_noon(dnums,fil_counts)

        return dnums_noon, daily_counts

    def fate_frac(self, dn, da, ednums, ecounts):
        esum = np.cumsum(ecounts)
        total = np.add(da['retained'],da['seaward'])
        # avoid double counting entrained particles by subtracting out entrained
        daily_agg_retained_alive = np.add(da['retained'],-esum)
        frac = {}
        frac['retained'] =  np.divide(daily_agg_retained_alive,total)
        frac['seaward'] =   np.divide(da['seaward'],total)
        frac['entrained'] = np.divide(esum,total)

        return frac

    def load_entrain_counts(self):
        entrain_dir = os.path.join(self.base_dir,'plot_entrainment')
        entrain_file = os.path.join(entrain_dir,'daily_'+self.group_name+'.csv')
        dn,cvp,swp,other = np.loadtxt(entrain_file,delimiter=',',skiprows=1,unpack=True)
        # shift to center of day for consistency in plotting distribution
        dnums = dn - 0.5 
        counts = np.add(cvp,swp,other)

        # don't return first index because it corresponds to the initial
        # time of the simulation so entrainment is not possible.
        return dnums[1:], counts[1:]
        
    def filtered_behavior_counts(self):
        behave_dir = os.path.join(self.base_dir,'plot_active_behavior')
        behave_file = os.path.join(behave_dir,self.group_name+'_btypes.csv')
        dnums = np.loadtxt(behave_file,delimiter=',',usecols=[0],dtype=np.float64,skiprows=1)
        counts_arr = np.loadtxt(behave_file,delimiter=',',usecols=np.arange(1,9),dtype=np.int32,skiprows=1)
        daily_counts = {}
        dt_hours = (dnums[1] - dnums[0])*24.
        for nb, bt in enumerate(beh_types):
            fil_counts = utils.Godin(counts_arr[:,nb],dt_hours)
            dnums_noon, daily_counts[bt] = utils.daily_at_noon(dnums, fil_counts)

        return dnums_noon, daily_counts

