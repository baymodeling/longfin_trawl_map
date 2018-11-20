'''
Created on Nov 19, 2018

@author: scott
'''
import matplotlib
import pylab
import numpy as np
import pdb
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox, TransformedBbox

matplotlib.rcParams['hatch.linewidth'] = 0.7
matplotlib.rcParams['hatch.color'] = 'w'

def plot_boxes(ax, fig, data, xy, boxsize, xylims, leg_args, frac=True, 
              alt_hatch=False, labels=[]):
    num_plots = len(data)
    fig.show()
    fig.canvas.draw()
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
            if len(labels) > 1:
                plotBWPlot(fig_coords, data[p,:],fig, plot_range,
                             alt_hatch=alt_hatch, labels=labels[p,:])
            else:
                plotBWPlot(fig_coords, data[p,:],fig, plot_range,
                             alt_hatch=alt_hatch)
            fig.canvas.draw()
    xy_leg = [589782.5317557553,4187778.3682879894] # move to main
    mod = len(leg_args['boxes']) / 4
    if len(leg_args['boxes']) % 4 != 0:
        mod += 1
    bb_data = Bbox.from_bounds(xy_leg[0]-boxsize[0]/2., xy_leg  [1], 
                               boxsize[0]* mod, boxsize[1])
    disp_coords = ax.transData.transform(bb_data)
    fig_coords= fig.transFigure.inverted().transform(disp_coords)
    if alt_hatch:
        boxes=leg_args['boxes']*2
    else:
        boxes=leg_args['boxes']
    legend_data = {"med": plot_range[1] * .5,
                   "q1": plot_range[1] * .25,
                   "q3": plot_range[1] * .75,
                   "whislo": plot_range[0],
                   "whishi": plot_range[1]}
    legend_array = []
    for i in range(len(boxes)):
        legend_array.append(legend_data)
    plotBWPlot(fig_coords, legend_array, fig, plot_range,
                 legend=True, alt_hatch=alt_hatch, 
                 xlabels=boxes, ylabel=leg_args['ylabel'])


    return 
    
    
def plotBWPlot(xys, box_vals, fig, y_range, legend=False, alt_hatch=False,
                 xlabels=[], ylabel=[], labels=[]):
    # Plots a box graphs with the given bar names and values at the x,y coordinates of the Delta map.
    
    #Create axes
    tot_box_vals = np.empty(0)
    tot_labels = np.empty(0)
    for item in box_vals:
        tot_box_vals = np.append(tot_box_vals, item)
    for item in labels:
        tot_labels = np.append(tot_labels, item)
    cmap_pars = pylab.cm.get_cmap('spring')
    colors=[cmap_pars(float(ng)/float(len(tot_box_vals))) for ng in range(len(tot_box_vals))]        
    if not legend:
        ax = fig.add_axes(Bbox(xys))
        ind = np.arange(len(tot_box_vals))
        box1 = ax.bxp(tot_box_vals, showfliers=False, patch_artist=True)
    
        for pn, patch in enumerate(box1['boxes']):
            patch.set(facecolor=colors[pn], edgecolor=colors[pn]) 
            plt.setp(box1['whiskers'][pn*2], color=colors[pn])
            plt.setp(box1['whiskers'][pn*2+1], color=colors[pn])
            plt.setp(box1['medians'][pn], color='black')
        ax.set_ylim(y_range[0],y_range[1])
        ax.patch.set_alpha(0) 
#         
        # annotate
        ymax = y_range[1]
#         for nbv,bv in enumerate(tot_box_vals):
#             if bv['whishi'] > ymax:
#                 plt.annotate("%.0E"%(bv['whishi']),[ind[nbv]-0.5,0.65*ymax],rotation=90)
        
#         ax.set_frame_on(False)
#         ax.xaxis.set_visible(False)
#         ax.yaxis.set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_yticklabels([])
        plt.tick_params(
            axis='both',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom=False,      # ticks along the bottom edge are off
            top=False,
            left=False,         # ticks along the top edge are off
            labelbottom=False,
            labelleft=False,
            labeltop=False) # labels along the bottom edge are off
        
        numBoxes = len(tot_box_vals)
        pos = np.arange(numBoxes) + 1
        if len(tot_labels) > 0:
            for tick, label in zip(range(numBoxes), tot_labels):
                ax.text(pos[tick], 0.05, label, ha='center', va='bottom', color='red', fontsize=7)
                
    else:
        ax = fig.add_axes(Bbox(xys))
#         ind = np.arange(5, (len(tot_box_vals) + 1)* 5, 5)
        ind = np.arange(len(tot_box_vals))
        widths = [.5] * len(tot_box_vals)
        box1 = ax.bxp(tot_box_vals,positions=ind,widths=widths,showfliers=False,patch_artist=True)
        for pn, patch in enumerate(box1['boxes']):
            patch.set(facecolor=colors[pn], edgecolor=colors[pn]) 
            plt.setp(box1['whiskers'][pn*2], color=colors[pn])
            plt.setp(box1['whiskers'][pn*2+1], color=colors[pn])
            plt.setp(box1['medians'], color='black')
        ax.set_ylim(y_range[0],y_range[1])
        ax.patch.set_alpha(0) 
        ax.set_frame_on(False)
        ax.xaxis.set_visible(True)
        ax.yaxis.set_visible(True)
        if alt_hatch:
            xticks = np.arange(0,len(tot_box_vals),5)+0.5
        else:
            xticks = ind
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels,rotation=90,ha='center')
        ax.set_yticks(ax.get_yticks()[::2])
        try:
            ytick_max = int(y_range[1])/100000*100000
            ax.set_yticks([0,ytick_max])
            exponent = np.log10(ytick_max)
            if exponent - int(exponent) == 0.:
                ax.set_yticklabels(['0','10$^%d$'%(exponent)])
        except OverflowError:
            ytick_max = int(y_range[1])
            ax.set_yticks([0,ytick_max])
            ax.set_yticklabels(['0','{0}'.format(ytick_max)])
        ax.set_ylabel(ylabel)
    
            