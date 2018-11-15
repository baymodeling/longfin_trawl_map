# -*- coding: utf-8 -*-
"""
@author: ed, laurel

Bar plotting utility functions

NOTES:
* Do not resize figure. This will cause plots to become misplaced.
"""

import matplotlib
import pylab
import numpy as np
import pdb
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

matplotlib.rcParams['hatch.linewidth'] = 0.7
matplotlib.rcParams['hatch.color'] = 'w'

def plot_bars(ax, fig, data, xy, boxsize, xylims, leg_args, frac=True, 
              alt_hatch=False):
    num_plots = len(data)
    # Determine plot limits
    if frac:
        plot_range = [0.,1.]
    else:
        #plot_range = [0,np.amax(data[np.where(np.isfinite(xy[:,0]))])]
        plot_range = [0,leg_args['max']]

    ax.set_xlim(xylims[0],xylims[1])
    ax.set_ylim(xylims[2],xylims[3])

    ax.set_aspect('equal', adjustable='box-forced')
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    #Plots bar plots at given locations (x centered over point, y bottom at point)
    for p in range(num_plots):
        if np.isfinite(xy[p,0]):
            bb_data = Bbox.from_bounds(xy[p,0]-boxsize[0]/2., xy[p,1], 
                                       boxsize[0], boxsize[1])
            disp_coords = ax.transData.transform(bb_data)
            # Ben - what is this doing? Why does it need fig and not ax?
            fig_coords = fig.transFigure.inverted().transform(disp_coords)
            
            plotBarGraph(fig_coords, data[p,:],fig, plot_range,
                         alt_hatch=alt_hatch)
      
    xy_leg = [596000.,4198000.] # move to main
    bb_data = Bbox.from_bounds(xy_leg[0]-boxsize[0]/2., xy_leg[1], 
                               boxsize[0], boxsize[1])
    disp_coords = ax.transData.transform(bb_data)
    fig_coords = fig.transFigure.inverted().transform(disp_coords)
    if alt_hatch:
        bars=leg_args['bars']*2
    else:
        bars=leg_args['bars']
    plotBarGraph(fig_coords, [plot_range[1]]*len(bars), fig, plot_range,
                 legend=True, alt_hatch=alt_hatch, 
                 xlabels=bars, ylabel=leg_args['ylabel'])


    return 
    
    
def plotBarGraph(xys, bar_vals, fig, y_range, legend=False, alt_hatch=False,
                 xlabels=[], ylabel=[]):
    # Plots a bar graphs with the given bar names and values at the x,y coordinates of the Delta map.
    
    # Colors for bars so they get plotted with the same color order
    colors = ['b','g','r','c','m','y','k'] # max of 7 bars per graph supported
    
    #Create axes
    ax = fig.add_axes(Bbox(xys))
    
    # Plot bars
    width = 1.
    ind = np.arange(len(bar_vals))
    bar1 = ax.bar(ind,bar_vals,width)
    for b,bar in enumerate(bar1):
        if alt_hatch:
            bar.set_color(colors[b/2])
            if b%2 == 1: # hatch pred
                #bar.set_hatch('xx')
                bar.set_alpha(0.5)
        else:
            bar.set_color(colors[b])

    #Format plot
    ax.set_ylim(y_range[0],y_range[1])
    ax.patch.set_alpha(0) 
    ax.set_frame_on(False)

    # annotate
    ymax = y_range[1]
    for nbv,bv in enumerate(bar_vals):
        if bv > ymax:
            plt.annotate("%.0E"%(bv),[ind[nbv]-0.5,0.65*ymax],rotation=90)

    if legend:
        ax.xaxis.set_visible(True)
        ax.yaxis.set_visible(True)
        if alt_hatch:
            xticks = np.arange(0,len(bar_vals),2)+0.5
        else:
            xticks = ind
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels,rotation=90,ha='center')
        ax.set_yticks(ax.get_yticks()[::2])
        ytick_max = int(y_range[1])/100000*100000
        ax.set_yticks([0,ytick_max])
        exponent = np.log10(ytick_max)
        if exponent - int(exponent) == 0.:
            ax.set_yticklabels(['0','10$^%d$'%(exponent)])
        ax.set_ylabel(ylabel)
    else:
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
    