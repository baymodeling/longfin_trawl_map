'''
Created on Dec 13, 2018

@author: scott
'''

import os
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import glob
import numpy as np
import pylab



def make_Daily_Growth_Plot(data_dir, target_growthrate, output_dir):
    file_form = '*.csv'
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    files = glob.glob(os.path.join(data_dir, file_form))

    date_Files = {}
    
    for dfile in files:
        s_dfile = os.path.basename(dfile).split('_')
        for component in s_dfile:
            if target_growthrate in component:
                date_Files[dt.datetime.strptime(s_dfile[3], '%Y-%m-%d')] = dfile
    
    groups = []
    i = 0
    cur = []
    while i < len(date_Files):
        if i % 5 == 0:
            if len(cur) > 0:
                groups.append(cur)
            cur = []
        cur.append(i)
        i += 1
        if i == len(date_Files):
            if i % 5 != 5:
                groups.append(cur)
    cur_max = 0
    bw_data = np.zeros(len(groups), dtype=object)     
    for g, group in enumerate(groups):
        bw_data[g] = np.append(bw_data[g], np.zeros(len(groups) -1, dtype=object))
        for group_idx, group_num in enumerate(group):
            cur = []
            filedate = sorted(date_Files.keys())[group_num]
            filepath = date_Files[filedate]
            obs_data = pd.read_csv(filepath, parse_dates=True)            
            for surv_idx, surv in enumerate(obs_data['survey'].values):
                cur.append(obs_data['q50'].values[surv_idx])
                if obs_data['q50'].values[surv_idx] > cur_max:
                    cur_max = obs_data['q50'].values[surv_idx]
            bw_data[g][group_idx] = cur
    
    
    
    legend_labels = []
    
    num_subplots = len(groups)    
    f,axs = plt.subplots(num_subplots, 1, figsize=(18,10))
    for g, group in enumerate(groups):
        v = g + 1
        legend_labels = []
        ax1 = plt.subplot(num_subplots,1,v)
        for i, idx in enumerate(group):
            cmap_pars = pylab.cm.get_cmap('spring')
            colors=[cmap_pars(float(ng)/float(len(group))) for ng in range(len(group))]   
            line1 = ax1.plot(bw_data[g][i], color=colors[i])
            legend_labels.append(sorted(date_Files.keys())[idx].strftime('%m-%d-%Y'))
        ax1.legend(legend_labels, loc=(1.01, 0))
        ax1.set_ylim(ymax=cur_max)
    
        if g != len(groups) - 1:
            ax1.set_xticks([])
        else:
            new_ticks = ['Survey {0}'.format(g + 1) for g in range(len(groups[0])+ 1)]
            plt.xticks(np.arange(len(groups[0])+1), new_ticks)
    plt.suptitle('Cohort Plots Growth Rate = {0}'.format(target_growthrate), horizontalalignment='center')
    # plt.xlabel('Surveys', fontweight='bold')
    figname = os.path.join(output_dir, 'Cohort_Plots_GR_{0}.png'.format(target_growthrate))
    plt.savefig(figname, dpi=400, facecolor='white',bbox_inches='tight')
    plt.close()
if __name__  == '__main__':
    data_dir = r'C:\git\longfin_trawl_map\2013'
    target_growthrate = '0.14'
    output_dir = 'GrowthRate'
    make_Daily_Growth_Plot(data_dir, target_growthrate, output_dir)
