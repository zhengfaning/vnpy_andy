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
from talib import abstract
import talib

print(talib.get_functions())
print(talib.get_function_groups())

palettes_colors = d3["Category20"][20]

xx = np.array([])
xx = np.append(xx, 1)
xx = np.append(xx, 2)

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
open = []
vol = []
for i,v in enumerate(bar_data):
    bar:BarData = v
    date[i] = bar.datetime.strftime("%m/%d %H:%M")
    date_index[bar.datetime] = i
    close.append(bar.close_price)
    high.append(bar.high_price)
    low.append(bar.low_price)
    plot_index.append(i)
    open.append(bar.open_price)
    vol.append(bar.volume)

inputs = {
    'open': np.array(open),
    'high': np.array(high),
    'low': np.array(low),
    'close': np.array(close),
    'volume': np.array(vol)
}
inputs2 = {
    'open': np.array(open[1112:1126]),
    'high': np.array(high[1112:1126]),
    'low': np.array(low[1112:1126]),
    'close': np.array(close[1112:1126]),
    'volume': np.array(vol[1112:1126])
}
func = abstract.Function("CDLEVENINGSTAR")
result = func(inputs2)
x = np.where(result != 0)
print(x)



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