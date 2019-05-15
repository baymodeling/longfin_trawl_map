'''
Created on Feb 18, 2019

@author: scott
'''
import os
from rmapy.utils.gis import polygons_w_attributes_from_shp as polys_from_shp
from stompy.grid import unstructured_grid
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import Bbox
import pylab
import datetime as dt
from shutil import copyfile

class LongfinMap(object):
    '''
    Class for plotting Longfin Trawl map data. Contains data for plot locations and regions.
    Set up data into appropriate dataFrames before using this class. Gets Automatically set up in the
    LongfinPlotter class.
    
    inputs:
    run_dir: Run directory containing ptm.grd file
    grd_file: Grid file, likely named 'ptm.grd'
    year: Year of the run. currently does not support multiyear data
    sizes: List of the upper and lower bound of the longfin sizes in mm. List is inclusive. ex: [6, 10]
    Groups: takes in a list of surveys/cohorts to be used for the plot. Each input data file needs its own list of data,
             aka if there are two input data sources, the surveys list should contain 2 lists (ex [[3,4,5,6], [1,2,3,4,5,6,7,8,9]])
             if there is only one data source, a single list suffices (ex [2,3,4,5])
             If there are multiple data sources and the user inputs a single list (see above), all data sources will
             use the selected surveys. 
    Group_Type: specifies the type of group that is used (survey vs cohort).
    '''

    def __init__(self,
                 run_dir,
                 grd_file,
                 year,
                 sizes,
                 Groups,
                 Group_Type):
        self.run_dir = run_dir
        self.grd_file = grd_file
        self.Year = year
        self.Sizes = sizes
        self.Groups = Groups
        self.GroupType = Group_Type
        self.compare = False
        self._get_inputs()

    def _get_inputs(self):
        '''
        Prime variables and data to be used across all cases, such as xylimits, hatching region shp, 
        and region coordinates for plotting.
        '''
        # inputs used across all CAMT cases
        self.xylims = [530000,661500,4138000,4295000]
        shp = r"Longfin_hatching_regions.shp"
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
        
        self.utm_dict = {'Central_Delta_and_Franks_Tract':[620453.7400469416,4212122.078372202],
            'Upper_Sacramento_River':[629749.8528383253,4244678.154020051],
            'North_and_South_Forks_Mokelumne_River':[633314.2013617393,4222644.2739934],
            'South_Delta':[642592.4377057501,4189918.7990992256],
            'Cache_Slough_Complex':[615123.5756282026,4262158.33897849],
            'Confluence':[606111.7244591176,4214227.897524303],
            'Suisun_Bay':[587330.4530226303,4207893.7344756285],
            'Carquinez_Strait':[571227.4604096551,4209182.676400363], 
            'Suisun_Marsh':[586210.4760883171,4225235.907484644],
            'San_Pablo_Bay':[553942.9282736651,4208647.568697553],
            'Petaluma':[540030.1280006216,4221490.153564978],
            'South_SF_Bay':[566963.8823753597,4165482.214004264],
            'Central_SF_Bay':[550375.5435882693,4192415.9683790025], 
            'Lower_South_SF_Bay':[586049.3904422284,4145683.2290003207], 
            'Napa_Sonoma':[556261.7283191724,4226662.861358802]}
        
#         self.xy_leg = [554742.1172539165,4275228.120412473]
        self.xy_leg = [547799.8896998921,4275000.017826721]

        return
    
    def _get_grid_masks(self, xylims):
        '''
        gets mask to clip grid plot
        '''
        
        g = self.grd
        centers = g.cells_center(refresh=True)
        g_mask = g.cell_clip_mask(xylims)
        e_mask = g.edge_clip_mask(xylims)
    
        return g_mask, e_mask
    
    def _get_Plot_Labels(self, Filtered_DataFrame):
        '''
        find data for each region plot. Returns list of labels.
        If a survey doesn't have data, a red 'x' is plotted. Else, its blank.
        '''
        
        Group = Filtered_DataFrame['Group']
        labels = np.chararray(len(Group))
        labels[:] = 'X'
        i = 0
        for index, row in Filtered_DataFrame.iterrows():
            if self.plotType == 'bar':
                if row['Abundance'] >= 0.0 and row['Density'] >= 0.0:
                    labels[i] = ''
            elif self.plotType == 'boxwhisker':
                if row['q5'] >= 0.0:
                    labels[i] = ''
            i += 1
        return labels
        
    def _get_Plot_Scale(self, DataFrame, Var):
        '''
        Gets the Max data for plot.
        Boxwhisker plots use the max from the q50 value, the mean
        Log plots will round the number off to look nice for exponents.
        '''
        
        if self.plotType == 'boxwhisker':
            max_val = max(DataFrame['q50'].values)
            len_max = (len(str(max_val).split('.')[0]) - 2) * -1
            scaler = round(max_val, len_max)
            
        elif self.plotType == 'bar':
            max_val = max(DataFrame[Var].values)
            len_max = (len(str(max_val).split('.')[0]) - 2) * -1
            scaler = round(max_val, len_max)
            
        elif self.plotType == 'timeseries':
            max_val = max(max(DataFrame['Values'].values))
            len_max = (len(str(max_val).split('.')[0]) - 2) * -1
            scaler = round(max_val, len_max)
            
        if self.Log:
            if str(max_val).split('.')[0][:len_max] != 10:
                num_zero = (len_max * -1) + 1
            scaler = int('10' + '0'*num_zero)
        
        return scaler
    

    
    def _get_Unique_Groups(self, DataFrame):
        '''
        Gets the number of unique groups in a dataset for legend plotting
        returns tuples containing each group name and its source file
        '''
    
        counted_Groups = []
        for index, row in DataFrame.iterrows():
            group = row['Group']
            source = row['Source']
            GroupSource = (group, source)
            if GroupSource not in counted_Groups:
                counted_Groups.append(GroupSource)
                
        return counted_Groups
        
    def _get_Plot_Legend_labels(self, GroupSources):
        '''
        Reads in the source files to figure out what the labels are for the legend.
        If the label is unknown, then ask the user what to use for that source file.
        If additional entries are wanting to be saved, add them to the if/elif/else loop
        if Hatch, entrainment or fractional_entrainment, the labels are just the group number.
        #TODO: carry these values over from the connect_sources function in the Longfin_Plotter_DataManager.py 
        '''
        unknown_Sources = {}
        plot_Legend = []
        for GroupSource in GroupSources: 
            
            Group = GroupSource[0]  
            source = os.path.basename(GroupSource[1])

            if 'sls' in source.lower():
                plot_Legend.append('SLS {0}'.format(int(Group)))
            elif '20mm' in source.lower():
                plot_Legend.append('20mm {0}'.format(int(Group)))
            elif 'computed' == source.lower():
                plot_Legend.append('Computed'.format(int(Group)))
            elif self.datatype in ['hatch', 'entrainment', 'fractional_entrainment']:
                plot_Legend.append(int(Group))
            else:
                if source not in unknown_Sources.keys():
                    print 'Unknown data source {0}'.format(os.path.basename(source))
                    unknown_ID = raw_input('Please enter a 3 letter ID for new data source: ')
                    plot_Legend.append('{0} {1}'.format(unknown_ID, int(Group)))
                    unknown_Sources[os.path.basename(source)] = unknown_ID
                else:
                    plot_Legend.append('{0} {1}'.format(unknown_Sources[os.path.basename(source)], int(Group)))
                    
        return plot_Legend
    
    def _get_Fig_Coordinates(self, fig, ax, XY, boxsize, mod=1.):
        '''
        Gets Coordinates and transforms them into percentages of the plot
        mod is for legend plots, if the plot has more than 4 surveys, another plot length is added for
        every 4 surveys to prevent crowding.
        '''
        
        bb = Bbox.from_bounds(XY[0]-boxsize[0]/2., XY[1], boxsize[0] * mod, boxsize[1])
        disp_coords = ax.transData.transform(bb)
        fig_coords = fig.transFigure.inverted().transform(disp_coords)
        
        return fig_coords
    
    def _get_Legend_size_Modifier(self, DataFrame, Var):
        '''
        Gets the legend modifier based on the amount of datasets.
        For ever 4 datasets, the plot gets longer in the x direction.
        Give comparison plots a little extra room
        This prevents labels and legend from becoming bunched.
        '''
        if self.plotType == 'bar':
            data_len = len(DataFrame[Var])
        elif self.plotType == 'boxwhisker':
            data_len = len(DataFrame['q5'])
        elif self.plotType == 'timeseries':
            data_len = 5
        if self.compare:
            data_len *= 1.5
        mod = data_len / 4
        if data_len % 4 != 0:
                mod += 1
        return mod
    
    def _getNumdays(self, dataFrame):
        '''
        Gets the number of days in the dataframe for time series plots
        '''
        return len(dataFrame['Days'])    
    
    def _make_Legend_Data(self, num_Groups, Plot_Maximum):
        '''
        Makes dummy legend data to look nice for legend plot.
        Bar plots will be a series of colored bar for each group, each at the maximum value.
        Boxwhisker plots will be a series of colored bars for each group. Each will have its q95 value at the plot max, and then
        perfectly proportional data depending on if it uses a log scale or not.
        Timeseries plots will be a series of evenly spaced vertical colored lines for each group.
        '''
        legend_data = []
        for i in range(num_Groups):
            if self.plotType == 'bar':
                legend_data.append(Plot_Maximum)
            elif self.plotType == 'boxwhisker':
                if self.Log:
                    plot_minimum = 1000. if Plot_Maximum > 10000 else 1.
                    legend_data.append({"med": 10**np.mean([np.log10(plot_minimum), np.log10(Plot_Maximum)]), #make a dummy legend with perfect data
                                       "q1": 10**(np.mean([np.log10(plot_minimum), np.mean([np.log10(plot_minimum), np.log10(Plot_Maximum)])])),
                                       "q3": 10**(np.mean([np.mean([np.log10(plot_minimum), np.log10(Plot_Maximum)]), np.log10(Plot_Maximum)])),
                                       "whislo": plot_minimum,
                                       "whishi": Plot_Maximum})
                else:
                    legend_data.append({"med": Plot_Maximum * .5, #make a dummy legend with perfect data
                                        "q1": Plot_Maximum * .25,
                                        "q3": Plot_Maximum * .75,
                                        "whislo": 0,
                                        "whishi": Plot_Maximum})
            elif self.plotType == 'timeseries':
                linescalar = float(Plot_Maximum * .95) / num_Groups
                datalevel = linescalar  * (i+1)
                legend_data.append([datalevel] * self.numdays)
        return legend_data
    
    def _draw_water_and_polys(self, fig, ax, xylims):
        '''
        Plots the grid in solid blue color, ie water
        '''

        g_mask, e_mask = self._get_grid_masks(xylims)
        blu = '#add8e6'
        grey = '#A9A9A9'
        gcoll = self.grd.plot_cells(mask=g_mask, facecolor=blu, 
                                    edgecolor=blu)
    
        # plot relevant polygons
        polys_from_shp.plot_polygons(self.plot_poly_dict,color=grey)

        return fig, ax
    
    def _configure_Legend(self, ax, Plot_maximum, Labels, Var):
        '''
        Configures the legend to make it pretty. 
        Removes axis, sets limits, and arranges the label format
        '''
        
        ax.set_ylim(0,Plot_maximum)
        ax.patch.set_alpha(0) 
        ax.set_frame_on(False)
        ax.xaxis.set_visible(True)
        ax.yaxis.set_visible(True)
        
        #set up xtick locations
        if self.plotType == 'bar':
            xticks = np.arange(0, len(Labels)* 10, 10)

        elif self.plotType == 'boxwhisker':
            if self.compare:
                xticks = list(np.arange(0, len(Labels)*1.5))
                del xticks[2::3]
            else:
                xticks = np.arange(len(Labels))
                
        elif self.plotType == 'timeseries':
            xlims = ax.get_xlim()
            xticks = np.arange(0, xlims[1], (round(xlims[1], -1)/2))
            
        else:
            xticks = np.arange(len(Labels))
            
        ax.set_xticks(xticks)
        
        #set up xtick labels
        if self.datatype in ['hatch', 'entrainment']:
            ax.set_xticklabels(Labels,ha='center',fontsize=8)
            
        elif self.datatype in [None, 'cohort']:
            ax.set_xticklabels(Labels,rotation=90,ha='center',fontsize=8)
            
        elif self.datatype in ['fractional_entrainment']:
            ax.set_xticklabels(Labels,rotation=90,ha='center', fontsize=8)

        #set up y ticks if log or not
        if self.Log:
            plot_minimum = 1000. if Plot_maximum > 10000 else 1.
            ax.set_yscale('log')
            ax.set_ylim(plot_minimum,Plot_maximum)
            ax.set_yticks([plot_minimum, 10**round(np.mean([np.log10(plot_minimum), np.log10(Plot_maximum)])), Plot_maximum])
        else:
            ax.set_yticks([0, Plot_maximum])
            ax.ticklabel_format(style='sci', axis='y', scilimits=(-2,2))
            
        #set up additional labels for specific plots
        if self.datatype in ['hatch', 'entrainment']:
            ax.set_xlabel('Cohort')
            ax.set_ylabel('Larvae')
        if self.datatype in ['fractional_entrainment']:
            ax.set_ylabel('Fraction Entrained')
        else:
            ax.set_ylabel(Var)
        
        
    def _configure_Subplot(self, ax, Plot_maximum):
        '''
        Makes plots pretty by setting limits and removing axis' lines
        '''

        ax.patch.set_alpha(0) 

        if self.plotType == 'bar':
            #remove all spines
            ax.set_frame_on(False)
            ax.xaxis.set_visible(False)
            ax.yaxis.set_visible(False)
            
        elif self.plotType == 'boxwhisker':
            #Remove all ticks and spines except the bottom line for whisker reference
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
            
        elif self.plotType == 'timeseries':
            #remove ticks and spines except bottom and left spines
            ax.set_frame_on(True)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
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
            
        if self.Log: #adjust plots if log..
            plot_minimum = 1000. if Plot_maximum > 10000 else 1.
            ax.set_ylim(plot_minimum,Plot_maximum)
            ax.set_yscale('log')
        else:
            ax.set_ylim(0,Plot_maximum)
    
    def _regionCheck(self, data):
        '''
        Checks to see if data exists in each region.
        Used for time series plots
        if no data, returns False so no plot is made.
        '''
        for item in data:
            if item != None:
                return True
        return False

    def _add_Legend_Subplot(self, ax, data, Var):
        '''
        Adds the Legend subplot and arranges the data.
        '''
        #set up the colors for each group
        if self.datatype in ['hatch', 'entrainment', 'fractional_entrainment']:
            cmap_pars = pylab.cm.get_cmap('winter') #blues
            colors=[cmap_pars(float(ng)/float(len(self.Total_Groups))) for ng in range(len(self.Total_Groups))]
        else:
            cmap_pars = pylab.cm.get_cmap('spring') #purple to yellow
            colors=[cmap_pars(float(ng)/float(len(self.Total_Groups))) for ng in range(len(self.Total_Groups))]
#         if self.datatype in ['hatch', 'entrainment', 'fractional_entrainment']:
#             cmap_pars = pylab.cm.get_cmap('winter') #blues
#             colors=[cmap_pars(float(ng)/float(len(data))) for ng in range(len(data))]
#         else:
#             cmap_pars = pylab.cm.get_cmap('spring') #purple to yellow
#             colors=[cmap_pars(float(ng)/float(len(data))) for ng in range(len(data))]
        data_diff = len(self.Total_Groups) - len(data)
        colors = colors[data_diff:]
        
        leg_data = np.asarray(data)
        
        if self.plotType == 'bar':
            #Bar plot legends are simple bars for each group
            data_pos = np.arange(0, len(data)* 10, 10)
            bar1 = ax.bar(data_pos, leg_data, width=8)
            for b, bar in enumerate(bar1):
                bar.set_color(colors[b])
                
        elif self.plotType == 'boxwhisker':
            #Boxwhisker legend plots are a series of boxwhiskers, spaced depending on comparisons or not.
            
            widths = [.5] * len(leg_data)

            if self.compare:
                #if we are comparing data, we need to arrange legend data to be in groups of 2.
                #ie, 1,2,skip,4,5,skip,7,8,skip, etc....
                data_pos = list(np.arange(0, len(leg_data)*1.5))
                del data_pos[2::3]
            else:
                #otherwise, just line them up normally
                data_pos = np.arange(len(leg_data))
                
            box1 = ax.bxp(leg_data, positions=data_pos, widths=widths, showfliers=False, patch_artist=True)
            if self.compare:
                #if we compare data, instead of each group being a different color, we color the observed data green
                #and the predicted data yellow/orange. 
                for pn, patch in enumerate(box1['boxes']):
                    if pn % 2 == 0:
                        patch.set(facecolor='orange', edgecolor='orange') 
                        plt.setp(box1['whiskers'][pn*2], color='orange') #Note, each whisker is its own entity
                        plt.setp(box1['whiskers'][pn*2+1], color='orange')
                        plt.setp(box1['medians'][pn], color='black') 
                    else:
                        patch.set(facecolor='green', edgecolor='green') 
                        plt.setp(box1['whiskers'][pn*2], color='green') #Note, each whisker is its own entity
                        plt.setp(box1['whiskers'][pn*2+1], color='green')
                        plt.setp(box1['medians'][pn], color='black') 
            else:
                #otherwise, color them according to the colorscale above
                for pn, patch in enumerate(box1['boxes']): #colors each survey its own color from the color scale
                    patch.set(facecolor=colors[pn], edgecolor=colors[pn]) 
                    plt.setp(box1['whiskers'][pn*2], color=colors[pn]) #Note, each whisker is its own entity
                    plt.setp(box1['whiskers'][pn*2+1], color=colors[pn])
                    plt.setp(box1['medians'][pn], color='black')
                    
        elif self.plotType == 'timeseries':
            #for timeseries data, just plot each line according to the group and its computed data.
            for i, dataseries in enumerate(data):
                leg, = ax.plot(dataseries, color=colors[i], label=(i+1))

    def _add_Legend(self, fig, ax, boxsize, DataFrame, Var, Plot_maximum, dates=None):
        '''
        Creates the Legend plot with dummy data using the plot max.
        Legend plots have a modified box size to make them longer in the event
        that there are many surveys, otherwise the labels get crowded.
        Legend then configured after to be pretty.
        '''
        
        Groups = self._get_Unique_Groups(DataFrame) #get tuples with group and source for each point of data for labels
        plot_Legend_labels = self._get_Plot_Legend_labels(Groups) #create labels depending on source
        
        mod = self._get_Legend_size_Modifier(DataFrame, Var) #figure out if we need to expand the legend
        if self.datatype in ['fractional_entrainment']: #if its a time series plot, make the plot a set size.
            boxsize = [15000.,15000.]
            new_xy_leg = [self.xy_leg[0] + (boxsize[1]/2), self.xy_leg[1] - (boxsize[1]/2)]
            fig_coords = self._get_Fig_Coordinates(fig, ax, new_xy_leg, boxsize, mod=mod)
        else:
            fig_coords = self._get_Fig_Coordinates(fig, ax, self.xy_leg, boxsize, mod=mod)
        
        axb = fig.add_axes(Bbox(fig_coords))
        
        legend_data = self._make_Legend_Data(len(plot_Legend_labels), Plot_maximum)
        
        self._add_Legend_Subplot(axb, legend_data, Var)
        
        if self.datatype in ['fractional_entrainment']:
            #if time series plot, the legend also has additional labels, such as on the right side and different bottom labels. 
            plot_Legenddate_labels = [dates[0].strftime('%d-%b-%Y'), dates[int(len(dates)/2)].strftime('%d-%b-%Y'), dates[-1].strftime('%d-%b-%Y')]
            self._configure_Legend(axb, Plot_maximum, plot_Legenddate_labels, Var)
            self._add_TS_legend_labels(axb, Plot_maximum, plot_Legend_labels, legend_data)
        else:
            self._configure_Legend(axb, Plot_maximum, plot_Legend_labels, Var)
            

    def _add_StartDate_Text(self, ax):
        '''
        Adds a small line of text to the plot stating that values are removed before a date
        if startDate capabilities are utilized
        '''
        if self.startDate > dt.datetime(1900,1,1):
            xloc = ax.get_xlim()[0] + ((ax.get_xlim()[1] - ax.get_xlim()[0]) * .65) 
            yloc = ax.get_ylim()[0] + ((ax.get_ylim()[1] - ax.get_ylim()[0]) * .05) 
                
            ax.text(xloc, yloc, '*Values before {0} removed.'.format(self.startDate.strftime('%m-%d-%Y')), size=6)

    def _add_GrowthText(self, ax, GrowthRate):
        '''
        Adds text on plot showing the amount of growth per day that was specified.
        '''
        if GrowthRate > 0:
            xloc = ax.get_xlim()[0] + ((ax.get_xlim()[1] - ax.get_xlim()[0]) * .65) 
            yloc = ax.get_ylim()[0] + ((ax.get_ylim()[1] - ax.get_ylim()[0]) * .1) 
                
            ax.text(xloc, yloc, 'Growth Rate = {0} mm/Day'.format(GrowthRate))
        
    def _add_Subplot(self, ax, DataFrame, Var, Plot_maximum, labels=[]):
        '''
        Adds Subplot for specified region to the plot window.
        Gets colors for data, then formats data and plots it.
        Then colors data to the colormap specified.
        Then adds red 'x' labels for missing data.
        Subplot is then configured to look pretty.
        '''
        if self.datatype in ['hatch', 'entrainment', 'fractional_entrainment']:
            cmap_pars = pylab.cm.get_cmap('winter')
            num_dataset_sources = len(DataFrame['Group'])
            colors=[cmap_pars(float(ng)/float(len(self.Total_Groups))) for ng in range(len(self.Total_Groups))]
        elif self.datatype in ['multipredicted']:
            cmap_pars = pylab.cm.get_cmap('winter')
            num_dataset_sources = len(list(set(DataFrame['Source'].tolist())))
            colors=[cmap_pars(float(ng)/float(len(self.Total_Groups))) for ng in range(len(self.Total_Groups))]
        else:
            cmap_pars = pylab.cm.get_cmap('spring')
            num_dataset_sources = len(DataFrame['Group'])
            colors=[cmap_pars(float(ng)/float(len(self.Total_Groups))) for ng in range(len(self.Total_Groups))]
#         if self.datatype in ['hatch', 'entrainment', 'fractional_entrainment']:
#             cmap_pars = pylab.cm.get_cmap('winter')
#             colors=[cmap_pars(float(ng)/float(len(DataFrame['Group']))) for ng in range(len(DataFrame['Group']))]
#         elif self.datatype in ['multipredicted']:
#             cmap_pars = pylab.cm.get_cmap('winter')
#             num_dataset_sources = len(list(set(DataFrame['Source'].tolist())))
#             colors=[cmap_pars(float(ng)/float(num_dataset_sources)) for ng in range(num_dataset_sources)]
#         else:
#             cmap_pars = pylab.cm.get_cmap('spring')
#             colors=[cmap_pars(float(ng)/float(len(DataFrame['Group']))) for ng in range(len(DataFrame['Group']))]
        
        data_diff = len(self.Total_Groups) - num_dataset_sources
        colors = colors[data_diff:]
        
        plt_pos = np.arange(len(DataFrame))
        
        
        if self.plotType == 'bar':
            plt_data = self._formatPlotData(DataFrame, Var=Var)
            bar1 = ax.bar(plt_pos, plt_data, width=.7)
            for b, bar in enumerate(bar1):
                bar.set_color(colors[b])
                
        elif self.plotType == 'boxwhisker':
            plt_data = self._formatPlotData(DataFrame)
            if self.compare:
                if self.datatype == 'mulitpredicted':
                    bw_pos = list(np.arange(0, len(DataFrame)*1.5))
                    del bw_pos[len(DataFrame)::(len(DataFrame) + 1)]
                    box1 = ax.bxp(plt_data, positions=bw_pos, showfliers=False, patch_artist=True)
                    i = 0
                    for pn, patch in enumerate(box1['boxes']):
                        patch.set(facecolor=colors[i], edgecolor=colors[i]) 
                        plt.setp(box1['whiskers'][pn*2], color=colors[i]) #Note, each whisker is its own entity
                        plt.setp(box1['whiskers'][pn*2+1], color=colors[i])
                        plt.setp(box1['medians'][pn], color='black')
                        if i == len(DataFrame):
                            i = 0
                        else:
                            i += 1
                else:
                    bw_pos = list(np.arange(0, len(DataFrame)*1.5))
                    del bw_pos[2::3]
                    box1 = ax.bxp(plt_data, positions=bw_pos, showfliers=False, patch_artist=True)
                    for pn, patch in enumerate(box1['boxes']):
                        if pn % 2 == 0:
                            patch.set(facecolor='orange', edgecolor='orange') 
                            plt.setp(box1['whiskers'][pn*2], color='orange') #Note, each whisker is its own entity
                            plt.setp(box1['whiskers'][pn*2+1], color='orange')
                            plt.setp(box1['medians'][pn], color='black') 
                        else:
                            patch.set(facecolor='green', edgecolor='green') 
                            plt.setp(box1['whiskers'][pn*2], color='green') #Note, each whisker is its own entity
                            plt.setp(box1['whiskers'][pn*2+1], color='green')
                            plt.setp(box1['medians'][pn], color='black') 
                        
            else:
                box1 = ax.bxp(plt_data, showfliers=False, patch_artist=True)
                for pn, patch in enumerate(box1['boxes']): #colors each survey its own color from the color scale
                    patch.set(facecolor=colors[pn], edgecolor=colors[pn]) 
                    plt.setp(box1['whiskers'][pn*2], color=colors[pn]) #Note, each whisker is its own entity
                    plt.setp(box1['whiskers'][pn*2+1], color=colors[pn])
                    plt.setp(box1['medians'][pn], color='black')
                    
        elif self.plotType == 'timeseries':
            plt_data = self._formatPlotData(DataFrame, Var=Var)
            for i, linedata in enumerate(plt_data):
                ts = ax.plot(linedata, color=colors[i])
        
        self._configure_Subplot(ax, Plot_maximum)
        
        if len(labels) > 0:
            if self.plotType == 'bar':
                rects = ax.patches
                for rect, label in zip(rects, labels):
                    ylims = plt.ylim()
                    height = ylims[0] * 1.005
                    if len(labels) > 10:
                        ax.text(rect.get_x() + rect.get_width() / 2, height, label,
                                ha='center', va='bottom', color='red', fontsize=5)
                    else:
                        ax.text(rect.get_x() + rect.get_width() / 2, height, label,
                                ha='center', va='bottom', color='red', fontsize=7)
            
                        
            elif self.plotType == 'boxwhisker':
                numBoxes = len(plt_data)
                if not self.compare:
                    pos = np.arange(numBoxes) + 1
                else:
                    pos = list(np.arange(0, numBoxes*1.5))
                    del pos[2::3]
                ylims = plt.ylim()
                if len(labels) > 10:
                    for tick, label in zip(range(numBoxes), labels):
                        ax.text(pos[tick], ylims[0] * 1.005, label, ha='center', va='bottom', color='red', fontsize=5)
                else:
                    for tick, label in zip(range(numBoxes), labels):
                        ax.text(pos[tick], ylims[0] * 1.005, label, ha='center', va='bottom', color='red', fontsize=7)
                    
    def _add_TS_legend_labels(self, axb, Plot_maximum, plot_Legend_labels, legend_data):
        '''
        If timeseries plot, the legend needs labels on the right side of the plot for the cohort numbers.
        '''
        axb2 = axb.twinx()
        axb2.set_ylim(0, Plot_maximum)
        
        axb2.spines['right'].set_visible(False)
        axb2.spines['top'].set_visible(False)
        leg_data = []
        leg_labels = []
        for i, data in enumerate(legend_data):
            leg_data.append(data[0])
            leg_labels.append(str(plot_Legend_labels[i]))
        axb2.set_yticks(leg_data)  
        axb2.set_yticklabels(leg_labels)
        axb2.set_ylabel(self.GroupType)
    
    def _formatPlotData(self, data, Var=None):
        '''
        Gets Data for one region for the appropriate variable into a numpy array for plotting.
        Log data is set to 1 if lower than 1. Less than 1 values cause negative values when
        plotted on a log scale.
        '''
        if self.plotType == 'boxwhisker':
            formatted_data = []
            i = 0
            for index, datacol in data.iterrows():
                formatted_data.append({})
                if self.Log:
                    formatted_data[i]['med'] = datacol['q50'] if datacol['q50'] >= 1 else 1
                    formatted_data[i]['q1'] = datacol['q25'] if datacol['q25'] >= 1 else 1
                    formatted_data[i]['q3'] = datacol['q75'] if datacol['q75'] >= 1 else 1
                    formatted_data[i]['whislo'] = datacol['q5'] if datacol['q5'] >= 1 else 1
                    formatted_data[i]['whishi'] = datacol['q95'] if datacol['q95'] >= 1 else 1
                else:
                    formatted_data[i]['med'] = datacol['q50']
                    formatted_data[i]['q1'] = datacol['q25']
                    formatted_data[i]['q3'] = datacol['q75']
                    formatted_data[i]['whislo'] = datacol['q5']
                    formatted_data[i]['whishi'] = datacol['q95']
                i += 1
                
            
            
        elif self.plotType == 'bar':
            formatted_data = np.asarray(data[Var])
            if self.Log:
                for i, data in enumerate(formatted_data):
                    if data < 1:
                        formatted_data[i] = 1.
                        
        elif self.plotType == 'timeseries':
            formatted_data = []
            for i, tsdata in enumerate(data['Values'].values):
                formatted_data.append(tsdata)
                        
        return formatted_data
                     
    
    def _findSiteLoc(self, sitename):
        '''
        Gets the coordinates for each region name
        '''
        return self.utm_dict[sitename]
    
    def _configure_Plot(self, fig, ax, Var):
        '''
        Takes an existing Plot object and makes it pretty. 
        Adds title, sets extents, and removes axis.
        '''
        ax.set_xlim(self.xylims[0],self.xylims[1])
        ax.set_ylim(self.xylims[2],self.xylims[3])
        ax.set_aspect('equal', adjustable='box-forced')
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        if self.datatype == 'hatch':
            title = '{0} Hatching'.format(self.Fishtype)
        elif self.datatype == 'entrainment':
            title = '{0} Entrainment'.format(self.Fishtype)
        elif self.datatype == 'fractional_entrainment':
            title = '{0} Fractional Entrainment'.format(self.Fishtype)
        elif self.datatype == 'cohort':
            title = '{0} Cohort {1}'.format(self.Fishtype, self.Cohort_Number)
        else:
            title = '{0} {1}mm to {2}mm {3}'.format(self.Fishtype, self.Sizes[0], self.Sizes[1], Var)
        if self.compare:
            if self.Cohort_Number != 'Total':
                title += ' Pred Vs Obs Cohort {0}'.format(self.Cohort_Number)
            else:
                title += ' Pred Vs Obs Cohort Total'
        if self.Chronological:
            title += ' Chronological'
        title += ' {0}'.format(self.Year)
        
        plt.title(title)
        
    def _create_Plot(self, Var):
        '''
        Creates the plot object frame. Includes adding the Water grids plot.
        Then configures the plot to remove borders, coords, etc etc
        '''
        fig = plt.figure(figsize=[10,10])
        ax = fig.add_subplot(111)
        self._draw_water_and_polys(fig, ax, self.xylims)
        self._configure_Plot(fig, ax, Var)
        return ax, fig
        

    def savePlot(self, Var):
        '''
        Sets up a plot name depending on variables
        '''
        if not os.path.exists(r'Plots'):
            os.mkdir(r'Plots')
        if self.datatype == None:
            filename = '{0}_{1}_Size_{2}mm-{3}mm_{4}'.format(self.Year, self.plotType, self.Sizes[0], self.Sizes[1], Var)
        elif self.datatype in ['hatch', 'entrainment', 'fractional_entrainment','multipredicted']:
            filename = '{0}_{1}_{2}_{3}'.format(self.Year, self.plotType, Var, self.datatype.title())
        elif self.datatype in ['cohort']:
            filename = '{0}_{1}_Size_{2}mm-{3}mm_{4}_Cohort{5}'.format(self.Year, self.plotType, self.Sizes[0], self.Sizes[1], Var, self.Cohort_Number)
        if self.compare:
            if self.Cohort_Number == 'Total':
                filename += '_PredVsObs_Total'
            else:
                filename += '_PredVsObs_Cohort{0}'.format(self.Cohort_Number)
        if self.Chronological:
            filename += '_Chronological'
        if self.Log:
            filename += '_Log'
        self.filename = 'Plots\{0}.png'.format(filename)
        plt.savefig(self.filename, dpi=900, facecolor='white',bbox_inches='tight')
        plt.close()
        plt.clf()
        
    def movePlot(self, destination_dir, addName=None):
        '''
        Copies and renames plot to new directory.
        '''
        print 'Moving file from {0} to {1}...'.format(os.path.split(self.filename)[0], destination_dir)
        if addName != None:
            copyfile(self.filename, os.path.join(destination_dir, os.path.basename(self.filename.split('.')[0] + '_{0}.png'.format(addName))))
        else:
            copyfile(self.filename, os.path.join(destination_dir, os.path.basename(self.filename)))
        
    def plot_bars(self, dataFrame, Var, GrowthRate, Chronological, Log, Fishtype, startDate, datatype=None, max=0.):
        '''
        Adds subplots for each specified region and adds a new subplot for the data.
        Takes in organized Pandas dataFrame grabs data based on Var.
        If Chronological, organizes data based on sample date.
        '''
        self.plotType = 'bar'
        self.startDate = startDate
        self.Log = Log
        self.Chronological = Chronological
        self.datatype = datatype
        self.Fishtype = Fishtype
        boxsize = [10000.,10000.] #Check this
        
        ax, fig = self._create_Plot(Var)

        if max > 0.:
            Plot_maximum = max
        else:
            Plot_maximum = self._get_Plot_Scale(dataFrame, Var)
        
        if self.Chronological:
            dataFrame = dataFrame.sort_values(['Region', 'PlotOrder', 'Group'])
        else:
            dataFrame = dataFrame.sort_values(['LoadOrder','Region', 'Group'])
        
        for region in self.plot_poly_dict.keys():

            region_data = dataFrame.query('Region=="{0}"'.format(region))

            labels = self._get_Plot_Labels(region_data)
            
            fig_coords = self._get_Fig_Coordinates(fig, ax, self._findSiteLoc(region), boxsize)
            axb = fig.add_axes(Bbox(fig_coords))
            
            
            self._add_Subplot(axb, region_data, Var, Plot_maximum, labels=labels)
            fig.show()
            fig.canvas.draw()
            
        self._add_Legend(fig, ax, boxsize, region_data, Var, Plot_maximum)
        self._add_GrowthText(ax, GrowthRate)
        self._add_StartDate_Text(ax)
        
    def plot_boxwhisker(self, dataFrame, Var, Chronological, Log, Fishtype, datatype=None, cohortNum=0, max=0.):
        '''
        Adds subplots for each specified region and adds a new subplot for the data.
        Takes in organized Pandas dataFrame grabs data based on Var.
        If Chronological, organizes data based on sample date.
        '''
        self.plotType = 'boxwhisker'
        self.Log = Log
        self.Chronological = Chronological
        self.Cohort_Number=cohortNum
        self.datatype = datatype
        self.Fishtype = Fishtype
        boxsize = [10000.,10000.] #Check this
        
        ax, fig = self._create_Plot(Var)
        
        if max > 0.:
            Plot_maximum = max
        else:
            Plot_maximum = self._get_Plot_Scale(dataFrame, Var)
        
        if Chronological:
            dataFrame = dataFrame.sort_values(['Region', 'PlotOrder', 'Group'])
        else:
            dataFrame = dataFrame.sort_values(['LoadOrder', 'Region', 'Group'])
        
        for region in self.plot_poly_dict.keys():

            region_data = dataFrame.query('Region=="{0}"'.format(region))

            labels = self._get_Plot_Labels(region_data)
            
            fig_coords = self._get_Fig_Coordinates(fig, ax, self._findSiteLoc(region), boxsize)
            axb = fig.add_axes(Bbox(fig_coords))
            
            
            self._add_Subplot(axb, region_data, Var, Plot_maximum, labels=labels)
            fig.show()
            fig.canvas.draw()
            
        self._add_Legend(fig, ax, boxsize, region_data, Var, Plot_maximum)
        
    def plot_ObsVsPred_Boxwhisker(self, dataFrame, Var, Chronological, Cohort_Number, Log, Fishtype, datatype=None, max=0.):
        '''
        Adds subplots for each specified region and adds a new subplot for the data.
        Takes in organized Pandas dataFrame grabs data based on Var.
        '''
        self.compare = True
        self.Log = Log
        self.plotType = 'boxwhisker'
        self.Chronological = Chronological
        self.Cohort_Number = Cohort_Number
        self.datatype = datatype
        self.Fishtype = Fishtype
        boxsize = [10000.,10000.] #Check this
        
        ax, fig = self._create_Plot(Var)
        
        if max > 0.:
            Plot_maximum = max
        else:
            Plot_maximum = self._get_Plot_Scale(dataFrame, Var)
        
        if self.datatype == 'multipredicted':
            dataFrame = dataFrame.sort_values(['Region', 'Group', 'LoadOrder'])
        else:
            dataFrame = dataFrame.sort_values(['Region', 'Group'])

        
        for region in self.plot_poly_dict.keys():

            region_data = dataFrame.query('Region=="{0}"'.format(region))

            labels = self._get_Plot_Labels(region_data)
            
            fig_coords = self._get_Fig_Coordinates(fig, ax, self._findSiteLoc(region), boxsize)
            axb = fig.add_axes(Bbox(fig_coords))
            
            self._add_Subplot(axb, region_data, Var, Plot_maximum, labels=labels)
            fig.show()
            fig.canvas.draw()
            
        self._add_Legend(fig, ax, boxsize, region_data, Var, Plot_maximum)
     
    def plot_timeseries(self, dataFrame, Var, date_data, Log, Fishtype, datatype=None, max=0.):
        '''
        Adds subplots for each specified region and adds a new subplot for the data.
        Takes in organized Pandas dataFrame grabs data based on Var.

        '''
        self.compare = False
        self.Log = Log
        self.Chronological = False
        self.plotType = 'timeseries'
        self.datatype = datatype
        self.Fishtype = Fishtype
        boxsize = [10000.,10000.] #Check this
        self.numdays = self._getNumdays(dataFrame)
        ax, fig = self._create_Plot(Var)
        
        if max > 0.:
            Plot_maximum = max
        else:
            Plot_maximum = self._get_Plot_Scale(dataFrame, Var)
        
        dataFrame = dataFrame.sort_values(['Region', 'Group'])

        
        for region in self.plot_poly_dict.keys():

            region_data = dataFrame.query('Region=="{0}"'.format(region))
            regionCheck = self._regionCheck(region_data['Values'].values)
            if regionCheck:
#                 labels = self._get_Plot_Labels(region_data)
                
                fig_coords = self._get_Fig_Coordinates(fig, ax, self._findSiteLoc(region), boxsize)
                axb = fig.add_axes(Bbox(fig_coords))
                self._add_Subplot(axb, region_data, Var, Plot_maximum)
                fig.show()
                fig.canvas.draw()
            
        
        self._add_Legend(fig, ax, boxsize, region_data, Var, Plot_maximum, dates=date_data)
          
        
        
        