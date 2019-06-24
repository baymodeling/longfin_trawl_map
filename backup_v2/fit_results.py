import os, sys
import numpy as np
import pdb

def get_line_following_header_string(lines, string):
    for nl,line in enumerate(lines):
        if string in line:
            return lines[nl+1]

class FitResults(object):

    def __init__(self,
                 group_name,
                 region_dicts,
                 rtime,
                 fit_dir):
        self.group_name = group_name
        self.region_dicts = region_dicts
        self.rtime = rtime
        self.fit_dir = fit_dir

    def set_dnums(self):
        dnums = []

        return dnums
    def load_entrain(self):
        # load output of fitting self.dnums, self.counts_dict
        fname = os.path.join(self.fit_dir,'ds.rep')
        fp = open(fname, 'rt')
        lines = fp.readlines()
        line = get_line_following_header_string(lines, '#Wavg_theta')
        Theta = [float(line.split()[0]), float(line.split()[1])]
        nl0 = lines.index('#N_Ent\n')
        nl1 = lines.index('#Wavg_theta\n')
        elines = lines[nl0+1:nl1]
        ent_individual = np.loadtxt(elines)
        #entrain_individual = np.multiply(en_individual,np.transpose(Theta))
        ecounts = np.sum(ent_individual,axis=0)

        return ecounts

    def load_region_counts(self):
        # load output of fitting self.dnums, self.counts_dict
        fname = os.path.join(self.fit_dir,'ds.rep')
        fp = open(fname, 'rt')
        lines = fp.readlines()
        nl0 = lines.index('#N\n')
        nl1 = lines.index('#Qx\n')
        clines = lines[nl0+1:nl1]
        counts = np.loadtxt(clines)

        return counts

def load_obs_regional_abundance(dat_file):
    # load data file input to fitting
    fp = open(dat_file, 'rt')
    lines = fp.readlines()
    line = get_line_following_header_string(lines, '#RegVol')
    reg_vol = [float(rv) for rv in line.split()]
    nl0 = lines.index('#Stn Reg Mday Cnt Vol Secchi Pday Trip\n')
    nl1 = lines.index('#obs_Sal\n')
    clines = lines[nl0+1:nl1]
    stn, reg, mday, cnt, vol, secchi, pday, trip = np.loadtxt(clines,unpack=True)
    nreg = len(reg_vol)
    trips = np.unique(trip)
    ntrips = len(trips)
    cnt_per_reg_trip = np.zeros((nreg,ntrips),np.float64)
    vol_per_reg_trip = np.zeros((nreg,ntrips),np.float64)
    density = np.zeros((nreg,ntrips),np.float64)
    reg_abundance = np.zeros((nreg,ntrips),np.float64)
    for nr0 in range(nreg):
        nr = nr0 + 1
        for nt0 in range(ntrips):
            nt = nt0 + 1
            indices = np.where(np.logical_and(reg==nr, trip==nt))
            cnt_per_reg_trip[nr0,nt0] = np.sum(cnt[indices])
            vol_per_reg_trip[nr0,nt0] = np.sum(vol[indices])
            density[nr0,nt0] = cnt_per_reg_trip[nr0,nt0]/vol_per_reg_trip[nr0,nt0]
            reg_abundance[nr0,nt0] = density[nr0,nt0]*reg_vol[nr0]

    return reg_abundance

if __name__ == '__main__':
    dat_file = r'..\fitting_max_pop_skt_sal\inputs\DS_Data_Dec-20-01_4m.txt'
    reg_ab = load_obs_regional_abundance(dat_file)
