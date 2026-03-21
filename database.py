import sqlite3, hashlib
import pandas as pd
from datetime import datetime

DB_NAME = 'memory_market.db'

def hash_pwd(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, qq TEXT, reg_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS price_history (brand TEXT, spec TEXT, platform TEXT, date TEXT, price REAL, url TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (username TEXT, brand TEXT, spec TEXT, platform TEXT)''')
    # 初始管理员 admin / admin123
    if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)", ('admin', hash_pwd('admin123'), 'admin', '10000', '2026-03-22'))
    conn.commit(); conn.close()

def get_real_data(brand, spec, platform):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT date as Date, price as Price, url as URL FROM price_history WHERE brand=? AND spec=? AND platform=? ORDER BY date ASC", conn, params=(brand, spec, platform))
    conn.close()
    if not df.empty: df['Date'] = pd.to_datetime(df['Date'])
    return df

def verify_login(u, p):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
    conn.close()
    if res and res[0] == hash_pwd(p): return True, res[1]
    return False, None

def add_favorite(u, b, s, p):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("INSERT INTO favorites VALUES (?,?,?,?)", (u, b, s, p))
    conn.commit(); conn.close()