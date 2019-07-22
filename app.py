import multiprocessing
from time import sleep
from datetime import datetime, time
from logging import INFO

from vnpy.event import EventEngine
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine

from vnpy.gateway.tiger import TigerGateway
from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.cta_strategy.base import EVENT_CTA_LOG
# from vnpy.app.script_trader import init_cli_trading
from vnpy.app.script_trader import ScriptEngine

SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True

def read_private_key(key_file):
    """
    Pem key
    :param key_file:
    :return:
    """
    key_str = open(key_file, 'r').read()
    return key_str.replace('-----BEGIN RSA PRIVATE KEY-----\n', '').replace(
        '\n-----END RSA PRIVATE KEY-----', '').strip()

class App(object):
    setting = {
        "tiger_id": "20150137",
        "account": "20190130122050760",
        "服务器": "仿真",
        "private_key": read_private_key('./money/rsa_private_key.pem'),
    }

    _instance = None

    @staticmethod
    def instance():
        if not App._instance:
            App._instance = App()
            print("创建App实例")
        return App._instance

    def __init__(self):
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        self.event_engine = event_engine
        self.main_engine = main_engine
        self.is_start = False
    
    def start(self):
        if not self.is_start:
            print("App进行初始化")
            self.main_engine.add_gateway(TigerGateway)
            cta_engine = self.main_engine.add_app(CtaStrategyApp)
            self.main_engine.write_log("主引擎创建成功")

            log_engine = self.main_engine.get_engine("log")
            self.event_engine.register(EVENT_CTA_LOG, log_engine.process_log_event)
            self.main_engine.write_log("注册日志事件监听")

            self.main_engine.connect(App.setting, "TIGER")
            self.main_engine.write_log("连接TIGER接口")
            self.main_engine.add_engine(ScriptEngine)
            self.script_engine = self.main_engine.get_engine("ScriptTrader")
            self.main_engine.write_log("Script")

            sleep(10)

            cta_engine.init_engine()
            self.main_engine.write_log("CTA策略初始化完成")

            cta_engine.init_all_strategies()
            sleep(60)   # Leave enough time to complete strategy initialization
            self.main_engine.write_log("CTA策略全部初始化")

            cta_engine.start_all_strategies()
            self.main_engine.write_log("CTA策略全部启动")
        else:
            print("App已进行过初始化")
        self.is_start = True
    
    def getEngine(self):
        return self.main_engine

    def getScriptEngine(self):
        return self.script_engine
