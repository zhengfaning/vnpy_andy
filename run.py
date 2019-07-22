from flask import Flask
import app as vnpy_app
from time import sleep
from flask import request
import json
import reloader
reloader.enable()
import handler
import script_handler
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/oplist')
def oplist():
    l = []
    for item in handler.op_list:
        l.append(item)
    l_str = ",".join(l)
    output = { "vn方法列表": l_str, }
    return json.dumps(output, ensure_ascii=False)

@app.route('/op')
def op():
    vnapp = vnpy_app.App.instance()
    args = request.args
    print(args)
    op = args["cmd"]
    app_args = args.copy()
    app_args.pop("cmd")
    app_args["engine"] = vnapp.getEngine()
    op_func = handler.op_list[op]
    result = op_func(app_args)
    return result

@app.route('/script')
def script():
    vnapp = vnpy_app.App.instance()
    args = request.args
    print(args)
    op = args["cmd"]
    app_args = args.copy()
    app_args.pop("cmd")
    app_args["engine"] = vnapp.getScriptEngine()
    op_func = script_handler.script_list[op]
    result = op_func(app_args)
    return result

@app.route('/reload')
def reload():
    reloader.reload(handler)
    reloader.reload(script_handler)
    return "重载方法"

@app.route('/init')
def init():
    vnapp = vnpy_app.App.instance()
    vnapp.start()
    return "初始化vnpy系统完成"


if __name__ == "__main__":
    # vnapp = vnpy_app.App.instance()
    # vnapp.run()
    app.run()
    print("ok")