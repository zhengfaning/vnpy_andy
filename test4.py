from vnpy.trader.database import database_manager
from abu.UtilBu.ABuRegUtil import calc_regress_deg, regress_y, regress_xy
from vnpy.trader.constant import Exchange, Interval
import datetime
import numpy as np 
from vnpy.trader.utility import load_json, save_json, extract_vt_symbol, round_to
from vnpy.app.cta_strategy import (
    TickData,
    BarData,
    BarGenerator,
    ArrayManager,
)
from bokeh.io import output_file, show
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Label
from bokeh.themes import built_in_themes
from bokeh.io import curdoc
from bokeh.palettes import d3, brewer, mpl
from bokeh.core.enums import colors
from bokeh.layouts import column, gridplot
from bokeh.models import WheelZoomTool
palettes_colors = d3["Category20"][20]


x = np.arange(3343, 3368)
print(x)

vt_symbol = "goog.SMART"
symbol, exchange = extract_vt_symbol(vt_symbol)

start_date = datetime.datetime(2019,7,20,20)
end_date = datetime.datetime(2019,8,27,20)
bar_data = database_manager.load_bar_data(
        symbol, exchange, Interval.MINUTE, start_date, end_date
    )

date_index = {}
close = []
date = {}
plot_index = []
high = []
low = []
for i,v in enumerate(bar_data):
    bar:BarData = v
    date[i] = bar.datetime.strftime("%m/%d %H:%M")
    date_index[bar.datetime] = i
    close.append(bar.close_price)
    high.append(bar.high_price)
    low.append(bar.low_price)
    plot_index.append(i)



close = np.array(close)
high = np.array(high)
low = np.array(low)
reg, y2 = regress_y(close, False)

plot = figure(aspect_scale=0.3, match_aspect=False,plot_width=1100, plot_height=450,x_axis_label="date", y_axis_label="high", tools="pan,reset,save,wheel_zoom,xwheel_zoom,ywheel_zoom")

plot.xaxis.major_label_overrides = date
plot.line(x = plot_index, y = close, color=palettes_colors[0], line_width=1.5)
deg_line = np.array([y2[0],y2[-1]])
deg_x = np.array([plot_index[0],plot_index[-1]])
plot.line(x = deg_x, y = deg_line, color=palettes_colors[8])
show(plot)
print(y2[0],y2[-1])
print("over")