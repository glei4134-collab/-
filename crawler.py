import sqlite3, random, time
import numpy as np
from datetime import datetime
import config

class StrongMemorySpider:
    def __init__(self): self.db_name = "memory_market.db"

    def get_refined_price(self, base, weight):
        # 模拟搜索结果中的 10 个价格，取中位数以获得“合适值”
        pool = [base * weight * random.uniform(0.95, 1.05) for _ in range(10)]
        return round(float(np.median(pool)), 2)

    def generate_url(self, b, s, p):
        kw = f"{b}+{s}".replace(" ", "+")
        return f"https://search.jd.com/Search?keyword={kw}" if p=="京东" else f"https://s.taobao.com/search?q={kw}"

    def run_sync(self):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        logs = []
        for brand, w in config.BRAND_WEIGHTS.items():
            for spec, base in config.BASE_PRICES.items():
                for plat in config.PLATFORMS:
                    price = self.get_refined_price(base, w)
                    url = self.generate_url(brand, spec, plat)
                    c.execute("INSERT INTO price_history VALUES (?,?,?,?,?,?)", (brand, spec, plat, today, price, url))
                    logs.append(f"✅ {brand} | ¥{price}")
        conn.commit(); conn.close()
        return logs

spider = StrongMemorySpider()