
from tigeropen.common.consts import Language
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.util.signature_utils import read_private_key

rsa_private_key = read_private_key('./money/rsa_private_key.pem')

def get_client_config():
    """
    https://www.itiger.com/openapi/info 开发者信息获取
    :return:
    """
    is_sandbox = False
    client_config = TigerOpenClientConfig(sandbox_debug=is_sandbox)
    client_config.private_key = rsa_private_key
    client_config.tiger_id = '20150137'
    client_config.account = None # 'U9923867'  # 环球账户
    client_config.standard_account = None  # 标准账户
    client_config.paper_account = '20190130122050760'  # 模拟账户
    client_config.language = Language.zh_CN
    return client_config

