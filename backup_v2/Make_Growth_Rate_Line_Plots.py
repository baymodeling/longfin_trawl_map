'''
Created on Dec 13, 2018

@author: scott
'''

from Plot_Series_of_GrowthRates import make_Daily_Growth_Plot
from Plot_Dated_GrowthRates import make_Single_Day_Growth_Plot
import datetime as dt

growth_Rates = ['0.15', '0.20', '0.23', '0.25']
data_dir = r'J:\Longfin\bar_plots\Delta_Smelt\1999'
output_dir = r'J:\Longfin\bar_plots\Delta_Smelt\1999'

for GR in growth_Rates:
    print GR
    make_Daily_Growth_Plot(data_dir, GR, output_dir)
    
# start_Date = dt.datetime(1999,3,1)
# end_Date = dt.datetime(1999,3,30)
# while start_Date <= end_Date:
#     print start_Date
#     make_Single_Day_Growth_Plot(data_dir, start_Date, output_dir)
#     start_Date += dt.timedelta(days=1)