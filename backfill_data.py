import sqlite3
import random
from datetime import datetime, timedelta
import config


def run_backfill(days=30):
    conn = sqlite3.connect('memory_market.db')
    c = conn.cursor()

    # 1. 清空旧数据（推倒重来最稳）
    c.execute("DELETE FROM price_history")

    today = datetime.now()
    records_count = 0

    print(f"正在回填 {days} 天的历史行情数据...")

    for i in range(days):
        current_date = (today - timedelta(days=days - i)).strftime("%Y-%m-%d")

        for brand, weight in config.BRAND_WEIGHTS.items():
            for spec, base_p in config.BASE_PRICES.items():
                for plat in config.PLATFORMS:
                    # 模拟市场小幅波动
                    vol = random.uniform(0.97, 1.03)
                    price = round(base_p * weight * vol, 2)

                    # 生成溯源地址
                    kw = f"{brand}+{spec}".replace(" ", "+")
                    url = f"https://search.jd.com/Search?keyword={kw}"

                    c.execute("INSERT INTO price_history VALUES (?,?,?,?,?,?)",
                              (brand, spec, plat, current_date, price, url))
                    records_count += 1

    conn.commit()
    conn.close()
    print(f"✅ 成功！已注入 {records_count} 条人民币价格数据。")


if __name__ == "__main__":
    run_backfill()