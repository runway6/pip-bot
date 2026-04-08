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
        print("❌ 错误: 缺少 TG_BOT_TOKEN 或 TG_CHAT_ID")
        sys.exit(1)

    print("启动浏览器抓取网页...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. 访问网页并等待网络加载完毕
            page.goto(URL, wait_until="networkidle", timeout=30000)
            
            # --- 可选逻辑：自动点击“加载更多” ---
            # (通常新开放的比赛会排在最上面，不需要展开。但为了绝对安全防止遗漏，保留展开逻辑)
            for i in range(5):
                load_more_btn = page.locator("text='加载更多'")
                if load_more_btn.count() > 0 and load_more_btn.first.is_visible():
                    print(f"-> 发现【加载更多】按钮，正在点击展开页面...")
                    load_more_btn.first.click()
                    page.wait_for_timeout(2000) # 等待 2 秒让卡片渲染
                else:
                    break
            # -----------------------------------
            
            # 2. 核心逻辑：全局搜索【加入竞赛】按钮
            join_btn_count = page.locator("text='加入竞赛'").count()
            print(f"-> 检测完毕，当前页面发现【加入竞赛】按钮数量: {join_btn_count}")
            
            # 3. 触发报警逻辑
            if join_btn_count > 0:
                msg = (
                    f"🚨 <b>PIP 锦标赛紧急抢坑报警！</b> 🚨\n\n"
                    f"👉 🟢 <b>页面出现了 {join_btn_count} 个【加入竞赛】按钮！</b>\n\n"
                    f"坑位正在快速消耗，请火速前往！\n"
                    f"<a href='{URL}'>🔗 点击立即直达网页</a>"
                )
                send_tg_msg(msg)
                print("🚨 已触发报警！")
            else:
                print("✅ 暂未发现开放的比赛（无加入按钮），继续潜伏。")
                
        except Exception as e:
            print(f"❌ 抓取过程中发生异常: {e}")
            send_tg_msg(f"⚠️ <b>PIP 监控脚本异常</b>\n网页无法正常加载或结构大改，请检查。")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    check_tournaments()
