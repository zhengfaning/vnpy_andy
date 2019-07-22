
import json

op_list = {}

def addop(name):
    def add(func):
        op_list[name] = func
        return func
    return add

@addop("init")
def init(args):
    # vnapp.start()
    return "初始化vnpy系统完成"

@addop("contracts")
def contracts(args):
    engine = args["engine"]
    contracts = engine.get_all_contracts()
    result = []
    result.append("<table> ")
    for obj in contracts:
        result.append("<tr> ")
        result.append("<td> ")
        result.append(obj.name)
        result.append("</td> ")
        result.append("<td> ")
        result.append(obj.symbol)
        result.append("</td> ")
        result.append("<td> ")
        result.append(obj.vt_symbol)
        result.append("</td> ")
        result.append("<td> ")
        result.append(obj.gateway_name)
        result.append("</td> ")
        result.append("</tr> ")
    result.append("</table> ")
    return "".join(result)

@addop("download")
def download(args):
    engine = args["engine"]
    contracts = engine.get_all_contracts()
    print(contracts)
    return "查询合约成功"

# op_list = { "init": init, "contracts": contracts, "download": download }