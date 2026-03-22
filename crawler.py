import sqlite3
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import config

class StrongMemorySpider:
    def __init__(self):
        self.db_name = "memory_market.db"
        self._init_db()
        # 伪装成真实浏览器，降低被拦截概率
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS price_history 
                     (brand TEXT, spec TEXT, platform TEXT, date TEXT, price REAL, url TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS crawler_logs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                      status TEXT, items_count INTEGER, error_msg TEXT)''')
        conn.commit()
        conn.close()

    def write_log(self, status, count=0, error=""):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("INSERT INTO crawler_logs (status, items_count, error_msg) VALUES (?, ?, ?)", 
                      (status, count, error))
            conn.commit()
            conn.close()
        except: pass

    def get_real_market_price(self, brand, spec, platform):
        """真实抓取逻辑：目前以京东为例示范"""
        keyword = f"{brand} {spec} 内存条".replace(" ", "+")
        url = f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8"
        
        # 淘宝反爬极严，暂时统一走京东接口或综合报价网演示
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 定位京东的价格标签 <div class="p-price"><i>xxx</i></div>
            price_tags = soup.select('.p-price i')
            if not price_tags:
                return None, url
                
            # 清洗数据并取中位数（过滤掉异常的超低价运费或天价商品）
            prices = []
            for tag in price_tags:
                txt = tag.text.strip()
                if txt.replace('.', '', 1).isdigit():
                    prices.append(float(txt))
            
            if prices:
                prices.sort()
                median_price = prices[len(prices)//2]
                return median_price, url
                
        except Exception as e:
            print(f"抓取 {brand} {spec} 时出错: {e}")
        return None, url

    def run_sync(self):
        print("🕷️ 启动全网真实抓取引擎...")
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_count = 0
        display_logs = []

        try:
            brands = list(config.BRAND_WEIGHTS.keys())
            specs = list(config.BASE_PRICES.keys())
            
            for brand in brands:
                for spec in specs:
                    # 真实网络请求需要节制，每次请求休眠 2 秒防止被封 IP
                    time.sleep(2) 
                    
                    price, url = self.get_real_market_price(brand, spec, "京东")
                    
                    if price:
                        # 插入真实数据（不再清空旧数据，而是追加每天的新数据）
                        c.execute("INSERT INTO price_history VALUES (?,?,?,?,?,?)", 
                                 (brand, spec, "京东", today_str, price, url))
                        total_count += 1
                        print(f"✅ 获取成功: {brand} {spec} -> ¥{price}")
                    else:
                        print(f"⚠️ 获取失败: {brand} {spec}")
                        
                display_logs.append(f"✅ {brand} 当日真实数据更新完毕")

            conn.commit()
            self.write_log("Success", count=total_count)
            print(f"🎉 今日真实行情抓取完毕，共 {total_count} 条。")
            
        except Exception as e:
            self.write_log("Failed", error=str(e))
        finally:
            conn.close()
            
        return display_logs

spider = StrongMemorySpider()
if __name__ == "__main__":
    spider.run_sync()
