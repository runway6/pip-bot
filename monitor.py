import os
import sys
from playwright.sync_api import sync_playwright
import requests

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
URL = "https://mm.pip.world/tournaments?lang=zh&tab=all"

def send_tg_msg(text):
    """发送 Telegram 报警消息"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ TG 报警发送成功")
        else:
            print(f"❌ TG 报警发送失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求 TG 接口异常: {e}")

def check_tournaments():
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("❌ 错误: 缺少 TG_BOT_TOKEN 或 TG_CHAT_ID 环境变量")
        sys.exit(1)

    print("启动浏览器抓取网页...")
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 访问网页，并等待网络闲置（确保 JS 加载完成）
            page.goto(URL, wait_until="networkidle", timeout=30000)
            
            # 显式等待目标元素出现，最多等 15 秒
            print("等待赛事列表渲染...")
            page.wait_for_selector('.tournament-board__title-name', timeout=15000)
            
            # 获取所有赛事标题元素
            elements = page.query_selector_all('.tournament-board__title-name')
            titles = [el.inner_text() for el in elements]
            print(f"网页中抓取到以下标题: {titles}")
            
            # 过滤出“创世杯”
            genesis_cups = [t for t in titles if "创世杯" in t]
            count = len(genesis_cups)
            has_vii = any("VII" in t for t in genesis_cups)
            
            print(f"-> 当前创世杯数量: {count}")
            print(f"-> 是否发现 VII: {has_vii}")
            
            # 核心策略：数量不是 6 个，或者发现了 VII，立刻报警
            if count != 6 or has_vii:
                msg = (
                    f"🚨 <b>PIP 锦标赛监控报警！</b> 🚨\n\n"
                    f"<b>当前创世杯数量:</b> {count} (预期: 6)\n"
                    f"<b>是否发现第七期:</b> {'是 ⚠️' if has_vii else '否'}\n\n"
                    f"请立即前往网页检查！\n"
                    f"<a href='{URL}'>👉 点击直达网页</a>"
                )
                send_tg_msg(msg)
            else:
                print("✅ 状态正常（数量为 6 且未发现 VII），继续潜伏。")
                
        except Exception as e:
            print(f"❌ 抓取过程中发生异常: {e}")
            # 如果网页结构大改，找不到元素也会走到这里，我们可以发个报错通知自己
            send_tg_msg(f"⚠️ <b>PIP 监控脚本异常</b>\n无法定位网页元素或加载超时，可能是网页结构已更改，请检查 GitHub Actions 日志。")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    check_tournaments()
