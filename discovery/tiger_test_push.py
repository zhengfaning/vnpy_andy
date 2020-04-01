from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.util.signature_utils import read_private_key
from tigeropen.push.push_client import PushClient
from client_config import get_client_config

import time

client_config = get_client_config()
# 定义响应资产变化的方法
def on_asset_change(account, data):
    print(10*'--', 'asset change', 10*'--')
    print(account, data)

# 定义响应持仓变化的方法
def on_position_change(account, data):
    print(10*'--', 'position change', 10*'--')
    print(account, data)

# 定义响应订单变化的方法
def on_order_change(account, data):
    print(10*'--', 'order change', 10*'--')
    print(account, data)

# 定义响应行情变化的方法
def on_quote_change(*args):
    print(args)



# 初始化 pushclient
protocol, host, port = client_config.socket_host_port
push_client = PushClient(host, port, use_ssl=(protocol == 'ssl'))

# 指定响应资产变化的方法
push_client.asset_changed = on_asset_change
# 指定响应持仓变化的方法
push_client.position_changed = on_position_change
# 指定响应订单变化的方法
push_client.order_changed = on_order_change
# 指定响应行情变化的方法
push_client.quote_changed = on_quote_change

# 连接 pushclient
push_client.connect(client_config.tiger_id, client_config.private_key)

# 订阅资产变化
push_client.subscribe_asset()
# 订阅持仓变化
push_client.subscribe_position()
# 订阅订单变化
push_client.subscribe_order()


time.sleep(100)

# 断开链接
push_client.disconnect()
