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
            page.goto(URL, wait_until="networkidle", timeout=30000)
            page.wait_for_selector('.tournament-board__title-name', timeout=15000)
            
            # --- 1. 抓取标题逻辑 ---
            elements = page.query_selector_all('.tournament-board__title-name')
            titles = [el.inner_text() for el in elements]
            target_cups = [t for t in titles if "创世杯" in t or "Genesis Cup" in t]
            count = len(target_cups)
            has_xi = any("XI" in t.split() for t in titles)
            
            # --- 2. 新增核心指标：检测【加入竞赛】按钮 ---
            # 使用 Playwright 的文本选择器，精确匹配页面上有没有这四个字
            join_btn_count = page.locator("text='加入竞赛'").count()
            has_join_btn = join_btn_count > 0

            print(f"-> 抓取到标题: {titles}")
            print(f"-> 目标赛事总数: {count} (预期: 10)")
            print(f"-> 发现第11期(XI): {has_xi}")
            print(f"-> 发现【加入竞赛】按钮: {has_join_btn} (数量: {join_btn_count})")
            
            # --- 3. 触发报警逻辑 ---
            # 只要数量不对，或者出现了 XI，或者出现了加入按钮，立马报警！
            if count != 10 or has_xi or has_join_btn:
                msg = (
                    f"🚨 <b>PIP 锦标赛紧急报警！</b> 🚨\n\n"
                    f"<b>触发原因：</b>\n"
                )
                if has_join_btn:
                    msg += f"👉 🟢 <b>页面出现了 {join_btn_count} 个【加入竞赛】按钮！快去抢！</b>\n"
                if count != 10:
                    msg += f"👉 📊 赛事总数变动: 当前 {count} 个 (原基准: 10)\n"
                if has_xi:
                    msg += f"👉 🆕 发现了新一期 Genesis Cup XI\n"

                msg += (
                    f"\n<a href='{URL}'>🔗 点击立即直达网页抢坑</a>"
                )
                send_tg_msg(msg)
            else:
                print("✅ 状态正常（无加入按钮，数量 10，无 XI），继续潜伏。")
                
        except Exception as e:
            print(f"❌ 抓取过程中发生异常: {e}")
            send_tg_msg(f"⚠️ <b>PIP 监控脚本异常</b>\n抓取失败，可能是页面加载超时或结构大改，请查阅日志。")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    check_tournaments()
