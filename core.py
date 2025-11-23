import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import random

class StockMonitor:
    def __init__(self, config_path='data/config.json'):
        self.config_path = config_path
        self.blocked_urls = set()  # 存储已经代理过的URL
        self.proxy_host = os.getenv("PROXY_HOST", None)  # 从环境变量读取
        self.load_config()


    # 加载配置文件
    def load_config(self):
        # 检查目录是否存在，不存在则创建
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        # 如果配置文件不存在，生成一个初始配置
        if not os.path.exists(self.config_path):
            self.create_initial_config()
            
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        self.frequency = int(self.config['config'].get('frequency', 300))  # 默认检查频率为300秒
        print("配置已加载")

    # 创建初始的配置文件
    def create_initial_config(self):
        default_config = {
            "config": {
                "frequency": 30,  # 默认检查频率为30秒
                "telegrambot": "",
                "chat_id": "",
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

        def fetch_flaresolverr(url):
            print(f"Using proxy for {url}")
            headers = {"Content-Type": "application/json"}
            data = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }
            response = requests.post(f'{self.proxy_host}/v1', headers=headers, json=data)
            return response, response.json()['solution']['response']

        try:

            if not self.proxy_host:
                response = requests.get(url, headers=headers)
                print(response.status_code)
                if response.status_code == 403:
                    print(f"Error fetching {url}: Status code {response.status_code}. Try to set host.")
                    return None
                content = response.content
            else:   
                # 如果设置了代理，进行代理逻辑
                if url in self.blocked_urls:
                    print('url in set')
                    # 如果URL在blocked_urls中，直接使用代理请求
                    response, content = fetch_flaresolverr(url)
                    # 5% 的概率删除该 URL
                    if random.random() < 0.05:
                        print(f"Random chance hit: Deleting {url} from blocked list.")
                        self.blocked_urls.remove(url)
                            
                else:
                    # 尝试非代理请求
                    response = requests.get(url, headers=headers)
                    content = response.content
                    
                    # 检查是否需要绕过Cloudflare
                    def is_cloudflare_challenge(content):
                        # 检查页面内容是否包含Cloudflare验证页面的特征
                        content_str = content.decode('utf-8', errors='ignore').lower()
                        cf_indicators = [
                            'cloudflare',
                            'checking your browser',
                            'please wait while we check your browser',
                            'enable javascript and cookies',
                            'ray id',
                            'cf-ray',
                            'security check',
                            'attention required',
                            'cloudflare to restrict access',
                            'ddos protection by cloudflare',
                            'challenge-platform',
                            'cf-browser-verification'
                        ]
                        return any(indicator in content_str for indicator in cf_indicators)
                    
                    # 如果返回403或检测到Cloudflare验证页面，使用代理
                    if response.status_code == 403 or is_cloudflare_challenge(content):
                        if response.status_code == 403:
                            print(f'Return status code {response.status_code}')
                        else:
                            print(f'Detected Cloudflare challenge page for {url}')
                        response, content = fetch_flaresolverr(url)
                        if response.status_code == 200:
                            self.blocked_urls.add(url)  # 记录该URL，未来通过代理访问
                # 如果最终响应状态不是200，输出错误并返回None
                if response.status_code != 200:
                    print(f"Error fetching {url} via proxy. Status code {response.status_code}")
                    return None

            # 再次检查是否包含Cloudflare验证特征（防止代理返回的仍是验证页）
            if is_cloudflare_challenge(content):
                print(f"Still detecting Cloudflare challenge for {url} after proxy.")
                return None

            # soup = BeautifulSoup(response.content, 'html.parser')
            soup = BeautifulSoup(content, 'html.parser')
            content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content
            
            # 获取页面标题用于调试
            page_title = soup.title.string.strip() if soup.title else "No Title"
            
            if '宝塔防火墙正在检查您的访问' in content_str:
                # todo: 绕过宝塔防火墙拦截
                print('被宝塔防火墙拦截')
                return None

            # 首先检查是否有指定class的div
            out_of_stock = soup.find('div', class_=alert_class)
            if out_of_stock:
                return False  # 缺货

            # 其次，检查页面中是否包含 'out of stock', '缺货' 这类文字
            out_of_stock_keywords = ['out of stock', '缺货', 'sold out', 'no stock', 'ausverkauft', '缺貨中']
            page_text = soup.get_text().lower()  # 获取网页的所有文本并转为小写
            for keyword in out_of_stock_keywords:
                if keyword in page_text:
                    return False  # 缺货

            # 最后，防止 Cloudflare "Just a moment..." 页面被误判为有货
            if "Just a moment" in page_title or "Cloudflare" in page_title or "Attention Required" in page_title:
                print(f"Detected Cloudflare title '{page_title}' for {url}. Treating as error.")
                return None

            # 调试：如果有货，打印标题以确认不是误报
            print(f"Check passed (In Stock). Page Title: {page_title}")

            return True  # 有货
            
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
            current_status = self.check_stock(url)

            # 如果状态发生变化，发送通知
            if current_status is not None and current_status != last_status:
                status_text = "有货" if current_status else "缺货"
                message = f"{name} 库存变动 {status_text}\n购买 {url}"
                self.send_message(message)

                # 更新库存状态
                self.config['stock'][name]['status'] = current_status
                has_change = True
            # 打印当前时间和摘要
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {name}: {'有货' if current_status else '缺货'}")

        if has_change:
            # 保存更新后的配置
            self.save_config()

    # 监控主循环
    def start_monitoring(self):
        print("开始库存监控...")
        while True:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 检测库存")
            try: self.update_stock_status()
            except Exception as e: print(f'循环中发生错误 {str(e)}')
            time.sleep(self.frequency)

    # 外部重载配置方法
    def reload(self):
        print("重新加载配置...")
        self.load_config()

# 示例运行
if __name__ == "__main__":
    monitor = StockMonitor()
    monitor.start_monitoring()
