import matplotlib.pyplot as plt
import mpl_finance as mpf
import pandas as pd
from mpl_finance import candlestick_ohlc
import matplotlib.dates as dts
# import bokeh.plotting as bp
import datetime
import itertools, logging
import numpy as np
from math import pi

__colorup__ = "red"
__colordown__ = "green"

g_only_draw_price = False

K_PLT_MAP_STYLE = [
    'b', 'c', 'g', 'k', 'm', 'r', 'y', 'w']

def draw_kl2(df: pd.DataFrame, minute=False,day_sum=False):

    # 为了示例清晰，只拿出前30天的交易数据绘制蜡烛图，
    part_df = df
    # fig, ax = plt.subplots(figsize=(14, 7))
    fig, ax1 = plt.subplots(figsize=(6, 6))
    qutotes = []

    if day_sum:
        # 端线图绘制
        qutotes = []
        for index, (d, o, c, l, h) in enumerate(zip(part_df.time, part_df.open, part_df.close,
        part_df.high, part_df.low)):
            d = index if minute else dts.date2num(d)
            val = (d, o, c, l, h)
            qutotes.append(val)
        # plot_day_summary_oclh接口，与mpf.candlestick_ochl不同，即数据顺序为开收低高
        mpf.plot_day_summary_oclh(
            ax1, qutotes, ticksize=5, colorup=__colorup__, colordown=__colordown__)
    else:
        # k线图绘制
        qutotes = []
        for index, (d, o, c, h, l) in enumerate(zip(part_df.time, part_df.open, part_df.close,
        part_df.high, part_df.low)):
            d = index if minute else dts.date2num(d)
            val = (d, o, c, h, l)
            qutotes.append(val)
        # mpf.candlestick_ochl即数据顺序为开收高低
        mpf.candlestick_ochl(ax1, qutotes, width=0.6,
                             colorup=__colorup__, colordown=__colordown__)
    # for index, (d, o, c, h, l) in enumerate(
    #         zip(part_df.time, part_df.open, part_df.close,
    #             part_df.high, part_df.low)):
    #     # 蜡烛图的日期要使用dts.date2num进行转换为特有的数字值
    #     # d = datetime.datetime.fromtimestamp(d / 1000)
    #     # d = dts.date2num(d)
    #     d = index
    #     # 日期，开盘，收盘，最高，最低组成tuple对象val
    #     val = (d, o, c, h, l)
    #     # 加val加入qutotes
    #     qutotes.append(val)
    # 使用mpf.candlestick_ochl进行蜡烛绘制，ochl代表：open，close，high，low
    # mpf.candlestick_ochl(ax, qutotes, width=0.6, colorup=__colorup__,
    #                      colordown=__colordown__)
    # ax.autoscale_view()
    # ax.xaxis_date()
    plt.show()


def _do_plot_candle(date, p_open, high, low, close, volume, view_index, symbol, day_sum, minute):
    """
    绘制不可交互的k线图
    param date: 融时间序列交易日时间，pd.DataFrame.index对象
    :param p_open: 金融时间序列开盘价格序列，np.array对象
    :param high: 金融时间序列最高价格序列，np.array对象
    :param low: 金融时间序列最低价格序列，np.array对象
    :param close: 金融时间序列收盘价格序列，np.array对象
    :param volume: 金融时间序列成交量序列，np.array对象
    :param symbol: symbol str对象
    :param day_sum: 端线图 matplotlib的版本有些有bug显示不对
    :param minute: 是否是绘制分钟k线图
    """
    # 需要内部import不然每次import abupy都有warning，特别是子进程很烦人
    try:
        # noinspection PyUnresolvedReferences, PyDeprecation
        import mpl_finance as mpf
        import matplotlib.dates as dts
    except ImportError:
        # 2.2 才会有
        # noinspection PyUnresolvedReferences, PyDeprecation
        import mpl_finance as mpf
        import matplotlib.dates as dts
    if not g_only_draw_price:
        # 成交量，价格都绘制
        # noinspection PyTypeChecker
        fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(20, 12))
    else:
        # 只绘制价格
        fig, ax1 = plt.subplots(figsize=(6, 6))
    if day_sum:
        # 端线图绘制
        qutotes = []
        for index, (d, o, c, l, h) in enumerate(zip(date, p_open, close, low, high)):
            d = index if minute else dts.date2num(d)
            val = (d, o, c, l, h)
            qutotes.append(val)
        # plot_day_summary_oclh接口，与mpf.candlestick_ochl不同，即数据顺序为开收低高
        mpf.plot_day_summary_oclh(
            ax1, qutotes, ticksize=5, colorup=__colorup__, colordown=__colordown__)
    else:
        # k线图绘制
        qutotes = []
        for index, (d, o, c, h, l) in enumerate(zip(date, p_open, close, high, low)):
            d = index if minute else dts.date2num(d)
            val = (d, o, c, h, l)
            qutotes.append(val)
        # mpf.candlestick_ochl即数据顺序为开收高低
        mpf.candlestick_ochl(ax1, qutotes, width=0.6,
                             colorup=__colorup__, colordown=__colordown__)
    if not g_only_draw_price:
        # 开始绘制成交量
        ax1.set_title(symbol)
        ax1.set_ylabel('ochl')
        ax1.grid(True)
        if not minute:
            ax1.xaxis_date()
        if view_index is not None:
            # 开始绘制买入交易日，卖出交易日，重点突出的点位
            e_list = date.tolist()
            # itertools.cycle循环使用备选的颜色
            for v, csColor in zip(view_index, itertools.cycle(K_PLT_MAP_STYLE)):
                try:
                    v_ind = e_list.index(v)
                except Exception as e:
                    # logging.exception(e)
                    logging.debug(e)
                    # 向前倒一个
                    v_ind = len(close) - 1
                label = symbol + ': ' + str(date[v_ind])
                ax1.plot(v, close[v_ind], 'ro', markersize=12, markeredgewidth=4.5,
                         markerfacecolor='None', markeredgecolor=csColor, label=label)
                # 因为candlestick_ochl 不能label了，所以使用下面的显示文字
                # noinspection PyUnboundLocalVariable
                ax2.plot(v, 0, 'ro', markersize=12, markeredgewidth=0.5,
                         markerfacecolor='None', markeredgecolor=csColor, label=label)
            plt.legend(loc='best')
        # 成交量柱子颜色，收盘价格 > 开盘，即红色
        # noinspection PyTypeChecker
        bar_red = np.where(close >= p_open, volume, 0)
        # 成交量柱子颜色，开盘价格 > 收盘。即绿色
        # noinspection PyTypeChecker
        bar_green = np.where(p_open > close, volume, 0)
        date = date if not minute else np.arange(0, len(date))
        ax2.bar(date, bar_red, facecolor=__colorup__)
        ax2.bar(date, bar_green, facecolor=__colordown__)
        ax2.set_ylabel('volume')
        ax2.grid(True)
        ax2.autoscale_view()
        plt.setp(plt.gca().get_xticklabels(), rotation=30)
    else:
        ax1.grid(False)
    
    """
        save 了就不show了
    """
    plt.show()


# def _do_plot_candle_html(date, p_open, high, low, close, symbol):
#     """
#     bk绘制可交互的k线图
#     :param date: 融时间序列交易日时间，pd.DataFrame.index对象
#     :param p_open: 金融时间序列开盘价格序列，np.array对象
#     :param high: 金融时间序列最高价格序列，np.array对象
#     :param low: 金融时间序列最低价格序列，np.array对象
#     :param close: 金融时间序列收盘价格序列，np.array对象
#     :param symbol: symbol str对象
#     :param save: 是否保存可视化结果在本地
#     """
#     mids = (p_open + close) / 2
#     spans = abs(close - p_open)

#     inc = close > p_open
#     dec = p_open > close

#     w = 24 * 60 * 60 * 1000

#     t_o_o_l_s = "pan,wheel_zoom,box_zoom,reset,save"

#     p = bp.figure(x_axis_type="datetime", tools=t_o_o_l_s, plot_width=1280, title=symbol)
#     p.xaxis.major_label_orientation = pi / 4
#     p.grid.grid_line_alpha = 0.3

#     p.segment(date.to_datetime(), high, date.to_datetime(), low, color="black")
#     # noinspection PyUnresolvedReferences
#     p.rect(date.to_datetime()[inc], mids[inc], w, spans[inc], fill_color=__colorup__, line_color=__colorup__)
#     # noinspection PyUnresolvedReferences
#     p.rect(date.to_datetime()[dec], mids[dec], w, spans[dec], fill_color=__colordown__, line_color=__colordown__)

#     bp.show(p)
    # if save:
    #     save_dir = os.path.join(K_SAVE_CACHE_HTML_ROOT, ABuDateUtil.current_str_date())
    #     html_name = os.path.join(save_dir, symbol + ".html")
    #     ABuFileUtil.ensure_dir(html_name)
    #     bp.output_file(html_name, title=symbol)

def plot_candle_stick(symbol, df: pd.DataFrame, minute=False,day_sum=False, view_index = None):
    date = []
    for v in df.time.values:
        d = datetime.datetime.fromtimestamp(v / 1000)
        date.append(d)
    dt = pd.DatetimeIndex(date)
    date = np.array(date)
    open = df.open.values
    high = df.open.values
    low = df.low.values
    close = df.close.values
    volume = df.volume.values
    # if not interactive:
    return _do_plot_candle(dt, open, high, low, close, volume, view_index, symbol, day_sum, minute)
    # else:
    #     return _do_plot_candle_html(dt, open, high, low, close, symbol)
    