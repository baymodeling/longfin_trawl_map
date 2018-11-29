'''
Created on Nov 26, 2018

@author: scott, ed, laurel
'''

import matplotlib
import pylab
import numpy as np
import pdb
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from rmapy.utils.gis import polygons_w_attributes_from_shp as polys_from_shp

matplotlib.rcParams['hatch.linewidth'] = 0.7
matplotlib.rcParams['hatch.color'] = 'w'

def draw_water_and_polys(grid, plot_poly_dict, xylims):

    fig = plt.figure(figsize=[10,10])
    ax = fig.add_subplot(111)

    # plot grid in solid blue color
    g_mask, e_mask = get_grid_masks(grid, xylims)
    blu = '#add8e6'
    grey = '#A9A9A9'
    gcoll = grid.plot_cells(mask=g_mask, facecolor=blu, 
                                edgecolor=blu)

    # plot relevant polygons
    polys_from_shp.plot_polygons(plot_poly_dict,color=grey)

    return fig, ax


def get_grid_masks(grid, xylims):
    g = grid
    centers = g.cells_center(refresh=True)
    g_mask = g.cell_clip_mask(xylims)
    e_mask = g.edge_clip_mask(xylims)

    return g_mask, e_mask


def plot_boxes(ax, fig, data, xy, boxsize, xylims, leg_args, frac=True, 
              alt_hatch=False, labels=[]):
    '''
    Functions similar to the map_w_bars plot. Takes in the following arguments:
    ax: plot frame, should already exist from draw_water_and_polys() in Longfin bar. Be sure that gets called first.
    fig: Figure frame, same as ax.
    data: numpy array that contains all of the data for every bar plot. formatted as such:
                        region -> Survey -> dict{med, q1, q3, whislo, whishi}
            9 regions with 9 surveys will end up being 81 dictionaries!
    xy: xy locations dictionary for each bar plot. Comes from findSiteLoc()
    boxsize: size of the plots. 10,000x10,000 looks good.
    xylims: plot x and y limits for frame reference
    leg_args: arguments for the plot legend labels
    labels: array of labels for the bar plots, containing x's for areas with missing data. Array of lists, region -> surveys
    
    the script will iterate through each region and plot each bar graph separately. It will convert the coords into ratios
    of the plot window. The plot needs to redraw each time or else it gets confused and the plots will be offset.
    After all the bar plots are plotted, the legend is plotted below those.
    '''
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

    #Plots box plots at given locations (x centered over point, y bottom at point)
    for p in range(num_plots):
        if np.isfinite(xy[p,0]):
            bb_data = Bbox.from_bounds(xy[p,0]-boxsize[0]/2., xy[p,1], 
                                       boxsize[0], boxsize[1])
            disp_coords = ax.transData.transform(bb_data)
            fig_coords = fig.transFigure.inverted().transform(disp_coords) #convert coords into ratios
            if len(labels) > 1:
                plotBWPlot(fig_coords, data[p,:],fig, plot_range,
                             alt_hatch=alt_hatch, labels=labels[p,:])
            else:
                plotBWPlot(fig_coords, data[p,:],fig, plot_range,
                             alt_hatch=alt_hatch)
            fig.canvas.draw()
    xy_leg = [589782.5317557553,4187778.3682879894] # move to main, Legend coords
    mod = len(leg_args['boxes']) / 4 # figure out how long to make the legend, every 4 items make more room
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
    legend_data = {"med": plot_range[1] * .5, #make a dummy legend with perfect data
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
    
        for pn, patch in enumerate(box1['boxes']): #colors each survey its own color from the color scale
            patch.set(facecolor=colors[pn], edgecolor=colors[pn]) 
            plt.setp(box1['whiskers'][pn*2], color=colors[pn]) #Note, each whisker is its own entity
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
            left=False,         # ticks along the edge are off
            labelbottom=False,
            labelleft=False,
            labeltop=False) # labels along the bottom edge are off
        
        numBoxes = len(tot_box_vals)
        pos = np.arange(numBoxes) + 1
        if len(tot_labels) > 0:
            for tick, label in zip(range(numBoxes), tot_labels):
                ax.text(pos[tick], 0.05, label, ha='center', va='bottom', color='red', fontsize=7)
                
    else: #legend plot
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

        except OverflowError: #if the max is too small, you get an overflow error. then just use the normal number
            ytick_max = int(y_range[1])
            ax.set_yticks([0,ytick_max])
            ax.set_yticklabels(['0','{0}'.format(ytick_max)])
        ax.set_ylim(y_range[0], ytick_max)
        ax.set_ylabel(ylabel)
    
def plot_bars(ax, fig, data, xy, boxsize, xylims, leg_args, frac=True, 
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
    plotType = leg_args['PlotType']
    if 'obspred_label' in leg_args.keys():
        ylabel = leg_args['obspred_label']
    else:
        ylabel = ''
    #Plots bar plots at given locations (x centered over point, y bottom at point)
    for p in range(num_plots):
        if np.isfinite(xy[p,0]):
            bb_data = Bbox.from_bounds(xy[p,0]-boxsize[0]/2., xy[p,1], 
                                       boxsize[0], boxsize[1])
            disp_coords = ax.transData.transform(bb_data)
            # Ben - what is this doing? Why does it need fig and not ax?
            fig_coords = fig.transFigure.inverted().transform(disp_coords)
            if len(labels) > 1:
                plotBarGraph(fig_coords, data[p,:],fig, plot_range, plotType,
                             alt_hatch=alt_hatch, labels=labels[p,:], ylabel=ylabel)
            else:
                plotBarGraph(fig_coords, data[p,:],fig, plot_range, plotType,
                             alt_hatch=alt_hatch, ylabel=ylabel)
            fig.canvas.draw()
    xy_leg = [589782.5317557553,4187778.3682879894] # move to main
    mod = len(leg_args['bars']) / 4
    if len(leg_args['bars']) % 4 != 0:
        mod += 1
#     bb_data = Bbox.from_bounds(xy_leg[0]-boxsize[0]/2., xy_leg[1], 
#                                boxsize[0], boxsize[1])
    bb_data = Bbox.from_bounds(xy_leg[0]-boxsize[0]/2., xy_leg  [1], 
                               boxsize[0]* mod, boxsize[1])
    disp_coords = ax.transData.transform(bb_data)
    fig_coords = fig.transFigure.inverted().transform(disp_coords)
    if alt_hatch:
        bars=leg_args['bars']*2
    else:
        bars=leg_args['bars']
    plotBarGraph(fig_coords, [plot_range[1]]*len(bars), fig, plot_range, plotType,
                 legend=True, alt_hatch=alt_hatch, 
                 xlabels=bars, ylabel=leg_args['ylabel'])


    return 
    
    
def plotBarGraph(xys, bar_vals, fig, y_range, plotType, legend=False, alt_hatch=False,
                 xlabels=[], ylabel=[], labels=[]):
    # Plots a bar graphs with the given bar names and values at the x,y coordinates of the Delta map.
    
    # Colors for bars so they get plotted with the same color order
#     colors = ['b','g','r','c','m','y','k', '#ff33cc', '#996633'] # max of 9 bars per graph supported

    #Create axes
    ax = fig.add_axes(Bbox(xys))
    tot_bar_vals = np.empty(0)
    tot_labels = np.empty(0)
    for item in bar_vals:
        tot_bar_vals = np.append(tot_bar_vals, item)
    for item in labels:
        tot_labels = np.append(tot_labels, item)
    
    cmap_pars = pylab.cm.get_cmap('spring')
    colors=[cmap_pars(float(ng)/float(len(tot_bar_vals))) for ng in range(len(tot_bar_vals))]
    # Plot bars
    if legend:
        width = 8.
    else:
#         width = 1.
        width = .7

    ind = np.arange(len(tot_bar_vals))
    if legend:
        ind = np.arange(0, len(tot_bar_vals)* 10, 10)
    bar1 = ax.bar(ind,tot_bar_vals,width)
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
#     for nbv,bv in enumerate(tot_bar_vals):
#         if bv > ymax:
#             plt.annotate("%.0E"%(bv),[ind[nbv]-0.5,0.65*ymax],rotation=90)
    
    if legend:
        ax.xaxis.set_visible(True)
        ax.yaxis.set_visible(True)
        if alt_hatch:
            xticks = np.arange(0,len(tot_bar_vals),2)+0.5
        else:
            xticks = ind
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels,rotation=90,ha='center')
#         ax.set_yticks(ax.get_yticks()[::2])
#         ax.set_yticks(ax.get_yticks())
#         ytick_max = int(y_range[1])/100000*100000
#         ax.set_yticks([0,ymax])
#         if plotType == 'Log':
#             ticks = [0]
#             tick = 10
#             while tick < ymax:
#                 ticks.append(tick)
#                 tick *= 10
#             ax.set_yticks(ticks)
            
        try:
            ytick_max = int(y_range[1])/100000*100000
            ax.set_yticks([0,ytick_max])
            exponent = np.log10(ytick_max)
            if exponent - int(exponent) == 0.:
                ax.set_yticklabels(['0','10$^%d$'%(exponent)])

        except OverflowError: #if the max is too small, you get an overflow error. then just use the normal number
            ytick_max = int(y_range[1])
            ax.set_yticks([0,ytick_max])
            ax.set_yticklabels(['0','{0}'.format(ytick_max)])
        exponent = np.log10(ytick_max)
        if exponent - int(exponent) == 0.:
            ax.set_yticklabels(['0','10$^%d$'%(exponent)])
        ax.set_ylim(y_range[0], ytick_max)
        ax.set_ylabel(ylabel)
    else:
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        ax.set_ylabel(ylabel,rotation=0)
#     if plotType == 'Log':
# #         ax.set_yscale("log", nonposy='clip')
#         plt.yscale('log')
    if len(tot_labels) > 0:
        rects = ax.patches
        for rect, label in zip(rects, tot_labels):
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, height, label,
                    ha='center', va='bottom', color='red', fontsize=7)
        
    