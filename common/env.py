# -*- encoding:utf-8 -*-
"""
    全局环境配置模块
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import re
import platform
import sys
import warnings
from enum import Enum
from os import path

import numpy as np
import pandas as pd

__author__ = '阿布'
__weixin__ = 'abu_quant'

"""暂时支持windows和mac os，不是windows就是mac os（不使用Darwin做判断），linux下没有完整测试"""
g_is_mac_os = platform.system().lower().find("windows") < 0 and sys.platform != "win32"
"""主进程pid，使用并行时由于ABuEnvProcess会拷贝主进程注册了的模块信息，所以可以用g_main_pid来判断是否在主进程"""
g_main_pid = os.getpid()
g_cpu_cnt = os.cpu_count()
"""pandas忽略赋值警告"""
pd.options.mode.chained_assignment = None
"""numpy，pandas显示控制，默认开启"""
g_display_control = True
if g_display_control:
    # pandas DataFrame表格最大显示行数
    pd.options.display.max_rows = 20
    # pandas DataFrame表格最大显示列数
    pd.options.display.max_columns = 20
    # pandas精度浮点数显示4位
    pd.options.display.precision = 4
    # numpy精度浮点数显示4位，不使用科学计数法
    np.set_printoptions(precision=4, suppress=True)

"""忽略所有警告，默认关闭"""
g_ignore_all_warnings = False
"""忽略库警告，默认打开"""
g_ignore_lib_warnings = True
if g_ignore_lib_warnings:
    # noinspection PyBroadException
    try:
        import matplotlib

        matplotlib.warnings.filterwarnings('ignore')
        matplotlib.warnings.simplefilter('ignore')
        import sklearn

        sklearn.warnings.filterwarnings('ignore')
        sklearn.warnings.simplefilter('ignore')
    except:
        pass
if g_ignore_all_warnings:
    warnings.filterwarnings('ignore')
    warnings.simplefilter('ignore')

# ＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊ 数据目录 start ＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
"""
    abu 文件目录根目录
    windows应该使用磁盘空间比较充足的盘符，比如：d://, e:/, f:///

    eg:
    root_drive = 'd://'
    root_drive = 'e://'
    root_drive = 'f://'
"""
root_drive = path.expanduser('~')
"""abu数据缓存主目录文件夹"""
g_project_root = path.join(root_drive, 'abu')
"""abu数据文件夹 ~/abu/data"""
g_project_data_dir = path.join(g_project_root, 'data')
"""abu日志文件夹 ~/abu/log"""
g_project_log_dir = path.join(g_project_root, 'log')
"""abu数据库文件夹 ~/abu/db"""
g_project_db_dir = path.join(g_project_root, 'db')
"""abu缓存文件夹 ~/abu/cache"""
g_project_cache_dir = path.join(g_project_data_dir, 'cache')
"""abu项目数据主文件目录，即项目中的RomDataBu位置"""
g_project_rom_data_dir = path.join(path.dirname(path.abspath(path.realpath(__file__))), '../RomDataBu')

"""abu日志文件 ~/abu/log/info.log"""
g_project_log_info = path.join(g_project_log_dir, 'info.log')

"""hdf5做为金融时间序列存储的路径"""
g_project_kl_df_data = path.join(g_project_data_dir, 'df_kl.h5')

_p_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir))


#  ＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊ 日志 start ＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊
# TODO 将log抽出来从env中
def init_logging():
    """
    logging相关初始化工作，配置log级别，默认写入路径，输出格式
    """
    if not os.path.exists(g_project_log_dir):
        # 创建log文件夹
        os.makedirs(g_project_log_dir)

    # 输出格式规范
    # file_handler = logging.FileHandler(g_project_log_info, 'a', 'utf-8')
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=g_project_log_info,
                        filemode='a'
                        # handlers=[file_handler]
                        )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # 屏幕打印只显示message
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


init_logging()

#  ＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊ 日志 end ＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊

g_plt_figsize = (14, 7)


def init_plot_set():
    """全局plot设置"""
    import seaborn as sns
    sns.set_context('notebook', rc={'figure.figsize': g_plt_figsize})
    sns.set_style("darkgrid")

    import matplotlib
    # conda 5.0后需要添加单独matplotlib的figure设置否则pandas的plot size不生效
    matplotlib.rcParams['figure.figsize'] = g_plt_figsize


init_plot_set()
