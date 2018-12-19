'''
Created on Dec 13, 2018

@author: scott
'''
import numpy as np
import os
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import glob

import pylab

def make_Single_Day_Growth_Plot(data_dir, target_day, output_dir):

#     import numpy as np
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    
    file_form = '*.csv'
    
    files = glob.glob(os.path.join(data_dir, file_form))
    
    date_Files = []
    
    for dfile in files:
        s_dfile = os.path.basename(dfile).split('_')
        for component in s_dfile:
            if target_day.strftime('%Y-%#m-%#d') == component:
                date_Files.append(dfile)
    
    
    
                
    bw_data = np.zeros(len(date_Files), dtype=object)
    for file_num, dfile in enumerate(date_Files):
        obs_data = pd.read_csv(dfile, parse_dates=True)
        bw_data[file_num] = np.append(bw_data[file_num], np.zeros(len(obs_data['survey'].values) - 1, dtype=object))
        for idx, surv in enumerate(obs_data['survey'].values):
            bw_data[file_num][idx] = obs_data['q50'].values[idx]
            
    legend_labels = []
    for s, set in enumerate(bw_data):
        cmap_pars = pylab.cm.get_cmap('spring')
        colors=[cmap_pars(float(ng)/float(len(set))) for ng in range(len(set))]   
        label_path = os.path.basename(date_Files[s]).split('_')
        legend_labels.append([g.split('grow')[1] for g in label_path if 'grow' in g][0])
        line1 = plt.plot(set, color=colors[s])
    
        
    plt.xlabel('Surveys', fontweight='bold')
    xlabels = []
    for surv in range(1, len(set) + 1):
        xlabels.append('Survey {0}'.format(surv))
    plt.xticks(range(len(set)), xlabels)
    plt.title('Cohort Plots {0}'.format(target_day.strftime('%m/%d/%Y')))
    figname = os.path.join(output_dir, 'Cohort_Plots_{0}'.format(target_day.strftime('%m_%d_%Y')))
    plt.legend(legend_labels)
    plt.savefig(figname, dpi=400, facecolor='white',bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    data_dir = r'C:\git\longfin_trawl_map\2013'
    output_dir = 'GrowthRate'
    target_day = dt.datetime(2013,3,2)
    make_Single_Day_Growth_Plot(data_dir, target_day, output_dir)