from flask import Flask, request, jsonify, render_template
from core import StockMonitor
import json
import threading



app = Flask(__name__)
monitor = StockMonitor()

# 避免冲突
app.jinja_env.variable_start_string = '<<'
app.jinja_env.variable_end_string = '>>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        data = request.json
        monitor.config['config'] = data
        # monitor.config['config']['frequency'] = data.get('frequency', 300)
        # monitor.config['config']['telegrambot'] = data.get('telegrambot', "")
        # monitor.config['config']['chat_id'] = data.get('chat_id', "")
        monitor.save_config()
        return jsonify({"status": "success", "message": "Config updated"})
    else:
        return jsonify(monitor.config['config'])

@app.route('/api/stocks', methods=['GET', 'POST', 'DELETE'])
def stocks():
    if request.method == 'POST':
        data = request.json
        stock_name = data['name']
        url = data['url']
        monitor.config['stock'][stock_name] = {"url": url, "status": False}
        monitor.save_config()
        return jsonify({"status": "success", "message": f"Stock '{stock_name}' added"})
    elif request.method == 'DELETE':
        stock_name = request.json['name']
        if stock_name in monitor.config['stock']:
            del monitor.config['stock'][stock_name]
            monitor.save_config()
            return jsonify({"status": "success", "message": f"Stock '{stock_name}' deleted"})
        return jsonify({"status": "error", "message": f"Stock '{stock_name}' not found"}), 404
    else:
        # 获取 stock 字典
        stocks = monitor.config['stock']
        
        # 将字典转化为数组
        stock_list = []
        for name, details in stocks.items():
            stock_item = {
                "name": name,
                "url": details["url"],
                "status": details["status"]
            }
            stock_list.append(stock_item)
        
        # 返回转化后的数组
        return jsonify(stock_list)

@app.route('/api/stocks/pause', methods=['POST'])
def pause_stock():
    stock_name = request.json['name']
    with open('web.config.json', 'r+') as f:
        web_config = json.load(f)
        paused_stocks = web_config.get('paused_stocks', [])
        if stock_name not in paused_stocks:
            paused_stocks.append(stock_name)
            web_config['paused_stocks'] = paused_stocks
            f.seek(0)
            json.dump(web_config, f, indent=4)
            f.truncate()
    return jsonify({"status": "success", "message": f"Stock '{stock_name}' paused"})

@app.route('/api/stocks/resume', methods=['POST'])
def resume_stock():
    stock_name = request.json['name']
    with open('web.config.json', 'r+') as f:
        web_config = json.load(f)
        paused_stocks = web_config.get('paused_stocks', [])
        if stock_name in paused_stocks:
            paused_stocks.remove(stock_name)
            web_config['paused_stocks'] = paused_stocks
            f.seek(0)
            json.dump(web_config, f, indent=4)
            f.truncate()
    return jsonify({"status": "success", "message": f"Stock '{stock_name}' resumed"})

if __name__ == '__main__':
    # monitor.start_monitoring()
    thread = threading.Thread(target=monitor.start_monitoring)
    thread.daemon = True  # 设置为后台线程，这样主线程退出时它会自动退出
    thread.start()
    app.run(debug=False,host='0.0.0.0')
