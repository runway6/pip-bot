import requests
import os
import sys

# 从 GitHub Secrets 中读取 Telegram 配置
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 🚨 【重要】你需要将这里替换为你抓包得到的真实 API 地址
API_URL = "https://api.pip.world/tournaments/list" # 这是一个占位符

def send_tg_msg(text):
    """发送 TG 报警消息"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Telegram 消息发送成功")
        else:
            print(f"❌ Telegram 发送失败: {response.text}")
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")

def check_tournaments():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        print("开始请求 API...")
        response = requests.get(API_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return

        data = response.json()
        
        # 🚨 【重要】这里的 data.get("data", []) 需要根据真实的 JSON 结构修改
        tournaments = data.get("data", []) 
        
        # 为了精准，我们只统计名字里带有“创世杯”的赛事，防止官方上了其他类型的活动干扰判断
        genesis_cups = [t for t in tournaments if "创世杯" in t.get("name", "")]
        current_count = len(genesis_cups)
        
        # 核心逻辑：如果数量不是 6 个，就报警！
        if current_count != 6:
            msg = (
                f"🚨 <b>PIP 赛事数量异常报警</b> 🚨\n\n"
                f"当前“创世杯”数量变动为: <b>{current_count}</b> 个！(原为 6 个)\n"
                f"可能有新一期赛事发布，请立即去网页检查状态。\n"
                f"<a href='https://mm.pip.world/tournaments?lang=zh&tab=all'>👉 点击直达网页</a>"
            )
            send_tg_msg(msg)
            print(f"发现异常！当前数量: {current_count}，已发送报警。")
        else:
            print("赛事数量正常 (6个)，继续潜伏。")
            
    except Exception as e:
        print(f"脚本运行出错: {e}")

if __name__ == "__main__":
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("❌ 缺少 TG_BOT_TOKEN 或 TG_CHAT_ID 环境变量！")
        sys.exit(1)
    
    check_tournaments()
