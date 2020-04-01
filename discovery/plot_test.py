import pandas as pd
import matplotlib.pyplot as plt
from bokeh.io import output_file, show
from bokeh.plotting import figure
# from bokeh.core.enums import colors
from bokeh.models import Label
from bokeh.models import Arrow, OpenHead, NormalHead, VeeHead
from bokeh.palettes import d3
plot = figure(plot_width=1100, plot_height=700)
x0 = [1,2,3,4,5]
l1 = [1,2,3,4,5]
l2 = [1.4,2.4,3.4,4.4,5.4]

colors = d3["Category20"][20]

print(colors)
plot.line(x=x0, y=l1, color=colors[3], line_width=0.5)
plot.triangle(x=1, y=2, color=colors[4], angle=0, size=20)
plot.triangle(x=1, y=3, color=colors[5], angle=15, size=20)
plot.triangle(x=1, y=4, color=colors[6], angle=30, size=20)
plot.triangle(x=1, y=5, color="black", angle=45, size=20)
plot.triangle(x=1, y=6, color=colors[8], angle=60, size=20)
plot.triangle(x=1, y=7, color=colors[9], angle=90, size=20)
plot.triangle(x=1, y=8, color=colors[10], angle=180, size=20)

# plot.text(x=6, y=8, text="123", x_offset=1, y_offset=1 )
show(plot)