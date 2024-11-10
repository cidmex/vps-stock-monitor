import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class StockMonitor:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.load_config()

    # 加载配置文件
    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        self.frequency = self.config['config'].get('frequency', 300)  # 默认检查频率为300秒
        self.telegram_token = self.config['config'].get('telegrambot')
        self.chat_id = self.config['config'].get('chat_id')  # Telegram 频道或群组ID
        print("配置已加载")

    # 保存配置文件
    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        print("配置已更新")

    # 检查商品库存状态
    def check_stock(self, url, alert_class="alert alert-danger error-heading"):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                out_of_stock = soup.find('div', class_=alert_class)
                return out_of_stock is not None  # True表示缺货，False表示有货
            else:
                print(f"Failed to fetch {url}: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    # 推送库存变更通知到 Telegram
    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        try:
            response = requests.get(url, params=payload)
            if response.status_code == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status_code}")
        except Exception as e:
            print(f"Error sending message: {e}")

    # 刷新配置文件中的库存状态
    def update_stock_status(self):
        has_change = False
        for name, item in self.config['stock'].items():
            url = item['url']
            last_status = item.get('status',False)

            # 检查库存状态
            current_status = self.check_stock(url)

            # 如果状态发生变化，发送通知
            if current_status is not None and current_status != last_status:
                status_text = "缺货" if current_status else "有货"
                message = f"商品 '{name}' 的库存状态已更改：{status_text}\n查看链接: {url}"
                self.send_telegram_message(message)

                # 更新库存状态
                self.config['stock'][name]['status'] = current_status
                has_change = True
            # 打印当前时间和摘要
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {name}: {'缺货' if current_status else '有货'}")

        if has_change:
            # 保存更新后的配置
            self.save_config()

    # 监控主循环
    def start_monitoring(self):
        print("开始库存监控...")
        while True:
            self.update_stock_status()
            time.sleep(self.frequency)

    # 外部重载配置方法
    def reload(self):
        print("重新加载配置...")
        self.load_config()

# 示例运行
if __name__ == "__main__":
    monitor = StockMonitor()
    monitor.start_monitoring()
