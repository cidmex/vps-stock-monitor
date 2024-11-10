import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

class StockMonitor:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.load_config()

    # 加载配置文件
    def load_config(self):
        # 如果配置文件不存在，生成一个初始配置
        if not os.path.exists(self.config_path):
            self.create_initial_config()
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        self.frequency = self.config['config'].get('frequency', 300)  # 默认检查频率为300秒
        print("配置已加载")

    # 创建初始的配置文件
    def create_initial_config(self):
        default_config = {
            "config": {
                "frequency": 300,  # 默认检查频率为300秒
                "telegrambot": "",
                "chat_id": "",
                "notificationType": "telegram"  # 默认通知方式为telegram
            },
            "stock": {}
        }

        # 将默认配置写入文件
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        print("配置文件已生成：", self.config_path)
        
    # 保存配置文件
    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        print("配置已更新")

    # 检查商品库存状态
    def check_stock(self, url, alert_class="alert alert-danger error-heading"):

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
        }

        try:
            response = requests.get(url,headers=headers,)
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

    # 推送库存变更通知到
    def send_message(self, message):
        # 获取通知类型
        notice_type = self.config['config'].get('notice_type', 'telegram')
        
        if notice_type == 'telegram':
            # 读取 Telegram 配置
            telegram_token = self.config['config'].get('telegrambot')
            chat_id = self.config['config'].get('chat_id')
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message
            }
            try:
                response = requests.get(url, params=payload)
                if response.status_code == 200:
                    print("Telegram message sent successfully")
                else:
                    print(f"Failed to send message via Telegram: {response.status_code}")
            except Exception as e:
                print(f"Error sending message via Telegram: {e}")
        
        elif notice_type == 'wechat':
            # 读取微信配置
            wechat_key = self.config['config'].get('wechat_key')  # 获取微信推送密钥
            if wechat_key:
                # 构建微信推送 URL
                url = f"https://xizhi.qqoq.net/{wechat_key}.send"
                payload = {
                    'title': '库存变更通知',
                    'content': message
                }
                try:
                    response = requests.get(url, params=payload)
                    if response.status_code == 200:
                        print(f"Message sent successfully to WeChat: {message}")
                    else:
                        print(f"Failed to send message via WeChat: {response.status_code}")
                except Exception as e:
                    print(f"Error sending message via WeChat: {e}")
            else:
                print("WeChat key not found in configuration.")
        
        elif notice_type == 'custom':
            # 读取自定义 URL 配置
            custom_url = self.config['config'].get('custom_url')
            if custom_url:
                # 替换自定义 URL 中的 message 参数
                custom_url_with_message = custom_url.replace("{message}", message)
                try:
                    response = requests.get(custom_url_with_message)
                    if response.status_code == 200:
                        print(f"Custom notification sent successfully: {message}")
                    else:
                        print(f"Failed to send custom message: {response.status_code}")
                except Exception as e:
                    print(f"Error sending custom message: {e}")
            else:
                print("Custom URL not found in configuration.")


    # 刷新配置文件中的库存状态
    def update_stock_status(self):
        has_change = False
        # print(self.config['stock'])
        for name, item in self.config['stock'].items():
            url = item['url']
            last_status = item.get('status',False)

            # 检查库存状态
            current_status = not self.check_stock(url)

            # 如果状态发生变化，发送通知
            if current_status is not None and current_status != last_status:
                status_text = "有货" if current_status else "缺货"
                message = f"{name} 库存变动 {status_text}\n购买 {url}"
                self.send_message(message)

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
