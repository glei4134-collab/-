import os
import subprocess
from datetime import datetime
import crawler  # 确保你的 crawler.py 在同级目录


def run_git_cmd(cmd):
    """执行 Git 命令并打印结果"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e.stderr}")


def main():
    print(f"🚀 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始本地抓取任务...")

    # 1. 执行爬虫 (这里会抓取真实的人民币价格)
    try:
        logs = crawler.spider.run_sync()
        print(f"✅ 抓取完成，获取到 {len(logs)} 条数据。")
    except Exception as e:
        print(f"❌ 爬虫执行崩溃: {e}")
        return

    # 2. 执行 Git 推送逻辑
    print("同步数据到 GitHub...")
    # 添加数据库文件
    run_git_cmd("git add memory_market.db")

    # 提交更改 (带上日期时间)
    commit_msg = f"Update market data: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run_git_cmd(f'git commit -m "{commit_msg}"')

    # 推送到 GitHub
    run_git_cmd("git push origin main")

    print("🎉 所有操作已完成，GitHub 数据已同步！")


if __name__ == "__main__":
    main()