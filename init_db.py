import sqlite3

def init_log_table():
    conn = sqlite3.connect('memory_market.db')
    cursor = conn.cursor()
    # 创建日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawler_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            items_count INTEGER,
            error_msg TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ 日志表已成功创建（或已存在）！")

if __name__ == "__main__":
    init_log_table()