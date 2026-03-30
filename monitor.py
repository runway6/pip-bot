import os, requests
from playwright.sync_api import sync_playwright

def send_tg(msg):
    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        except:
            print("TG发送失败")

def run():
    print("--- 启动 PIP World 比赛监控 ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            # 直接进入你提供的比赛列表页
            target_url = "https://mm.pip.world/tournaments?lang=zh&tab=all"
            print(f"正在访问: {target_url}")
            page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # 给页面 20 秒加载时间，Web3 页面通常加载较慢
            print("等待比赛列表加载...")
            page.wait_for_timeout(20000) 

            # --- 监控策略：统计比赛卡片 ---
            # 观察页面，每个比赛通常都有“奖金”或“参与”按钮
            # 我们统计页面上出现的“详情”或“Details”按钮数量，或者特定的卡片特征
            # 这里建议统计包含“Prize”或“奖金”字样的区块
            cards = page.locator("button:has-text('详情'), button:has-text('Details'), div.tournament-card")
            count = cards.count()
            
            print(f"当前页面检测到比赛数量: {count}")

            # 假设目前常驻的比赛是 2 个，如果变成 3 个就报警
            # 你可以根据实际看到的比赛数量修改下面这个数字
            if count > 2: 
                print(f"🚨 发现新比赛！当前总数: {count}")
                send_tg(f"🏆 **PIP World 新比赛预警！**\n\n检测到当前共有 **{count}** 个比赛项目。\n\n[点击立即参加]({target_url})")
            else:
                print(f"✅ 状态正常：当前有 {count} 个比赛，暂无新增。")
                
        except Exception as e:
            print(f"脚本运行出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
