# Stock Monitor

`Stock Monitor` 是一个简单的 Python 库存监控工具，使用 Telegram API 发送库存变更通知。通过定期检查商品页面，判断商品是否缺货，并在状态变化时发送通知到指定的 Telegram 频道或群组。

## 功能概述

- **库存监控**：定期检查商品库存状态，根据网页中特定 HTML 元素是否存在来判断商品是否缺货。
- **Telegram 通知**：当库存状态变化时，向指定的 Telegram 频道或群组发送消息。
- **实时更新配置**：支持配置文件的实时加载与保存，通过 `reload()` 方法可以手动重载配置。
- **自动记录**：每次监控周期结束后，记录当前时间和库存状态。

## 安装

1. 克隆项目到本地或直接下载。
2. 确保安装以下依赖：

    ```bash
    pip install requests beautifulsoup4
    ```

3. 创建并配置 `config.json` 文件。

## 配置文件 (`config.json`)

`config.json` 是项目的配置文件，格式如下：

```json
{
    "config": {
        "frequency": 300,  # 监控频率（秒）
        "telegrambot": "YOUR_TELEGRAM_BOT_TOKEN",
        "chat_id": "YOUR_TELEGRAM_CHAT_ID"
    },
    "stock": {
        "商品1": {
            "url": "https://example.com/item1",
            "status": false
        },
        "商品2": {
            "url": "https://example.com/item2",
            "status": true
        }
    }
}
```

### 配置项说明

- **frequency**：监控周期，单位为秒，默认为 300 秒。
- **telegrambot**：Telegram 机器人令牌，用于发送通知。
- **chat_id**：Telegram 频道或群组 ID，用于接收通知。
- **stock**：商品列表，包含商品名称、商品页面 URL 和库存状态（`true` 表示缺货，`false` 表示有货）。

## 使用说明

### 启动监控

在终端运行以下命令启动库存监控：

```bash
python core.py
```

### 重新加载配置

可以通过调用 `reload()` 方法来重新加载 `config.json` 的配置。示例如下：

```python
from core import StockMonitor

monitor = StockMonitor()
monitor.reload()  # 重新加载配置
```

### 输出示例

每次监控循环结束后，程序会打印当前时间和商品的库存状态，例如：

```
2024-11-10 12:00:00 - 商品1: 缺货
2024-11-10 12:00:00 - 商品2: 有货
配置已更新
```

## 项目结构

- `core.py`：库存监控主程序，包含 `StockMonitor` 类的实现。
- `config.json`：项目的配置文件，存储监控商品列表和 Telegram 配置。

## 注意事项

1. **确保 Telegram Bot 已被加入到指定频道或群组**，并有发言权限。
2. **请正确配置 `config.json`** 文件，特别是 `telegrambot` 和 `chat_id` 参数。
3. 使用前确保商品页面上的缺货元素（如 `<div class="alert alert-danger error-heading">`）的 HTML 结构未更改。
