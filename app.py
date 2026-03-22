import streamlit as st
import database as db
import engine, config, crawler, dev_tools
import plotly.graph_objects as go
import pandas as pd
import sqlite3

# 初始化配置
st.set_page_config(page_title="AI 内存决策终端", layout="wide")
db.init_db()
dev_tools.enable_admin_bypass()  # 🌟 开启默认管理员进入
device, d_name = engine.get_device()

# UI 样式
st.markdown("""
<style>
    .price-val { color: #00FF00; font-size: 28px; font-weight: bold; }
    .status-success { color: #2ecc71; font-weight: bold; }
    .status-failed { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if st.session_state.get('username'):
    with st.sidebar:
        st.title("🛡️ 决策终端")
        st.write(f"用户: {st.session_state['username']} ({st.session_state['role']})")
        dev_tools.show_debug_sidebar()

    t_data, t_admin = st.tabs(["📊 价格趋势 (RMB)", "⚙️ 系统管理"])

    # --- 1. 价格趋势标签页 ---
    with t_data:
        st.header("🎯 内存价格 AI 预测分析")
        c1, c2, c3 = st.columns(3)
        sb = c1.multiselect("品牌", list(config.BRAND_WEIGHTS.keys()), default=["海力士"])
        ss = c2.selectbox("规格", list(config.BASE_PRICES.keys()))
        sp = c3.selectbox("平台", config.PLATFORMS)

        if st.button("🤖 执行 AI 深度预测", type="primary", use_container_width=True):
            fig = go.Figure()
            cols = st.columns(len(sb))
            for i, b in enumerate(sb):
                df_h = db.get_real_data(b, ss, sp)
                if not df_h.empty:
                    # 获取 AI 预测
                    df_p, acc = engine.predict_future_prices_pytorch(df_h, f"{b}_{ss}", device)

                    # 绘制实测线
                    fig.add_trace(go.Scatter(x=df_h['Date'], y=df_h['Price'], name=f"{b}-实测"))

                    # 检查预测数据并绘线
                    if not df_p.empty and 'Date' in df_p.columns:
                        fig.add_trace(
                            go.Scatter(x=df_p['Date'], y=df_p['Pred'], name=f"{b}-预测", line=dict(dash='dot')))
                        with cols[i]:
                            st.metric(label=f"📈 {b} 预测信心度", value=f"{acc:.1f}%")
                    else:
                        with cols[i]:
                            st.warning(f"⚠️ {b} 历史数据不足，AI 暂无趋势线")

                    # 展示价格卡片
                    st.markdown(f"{b} 最新价: <span class='price-val'>¥{df_h['Price'].iloc[-1]}</span>",
                                unsafe_allow_html=True)
                    st.link_button(f"🔗 查证 {sp} 原始网页", df_h['URL'].iloc[-1], use_container_width=True)

            st.plotly_chart(fig, use_container_width=True)

    # --- 2. 系统管理标签页 (管理员后台) ---
    with t_admin:
        if st.session_state['role'] == 'admin':
            st.header("⚙️ 终端管理控制台")

            # 操作区
            col_ctrl, col_info = st.columns([1, 2])
            with col_ctrl:
                st.subheader("🚀 数据同步")
                if st.button("🕸️ 启动全网同步 (中位数算法)", use_container_width=True):
                    with st.spinner("正在注入实时数据..."):
                        logs = crawler.spider.run_sync()
                        st.success("同步完成，品牌价格矩阵已更新。")
                        st.rerun()  # 刷新页面以显示最新日志

            # 日志监控区
            st.divider()
            st.subheader("🛡️ 爬虫运行日志 (最近 10 次)")

            try:
                conn = sqlite3.connect('memory_market.db')
                # 读取最近10条日志
                df_logs = pd.read_sql_query(
                    "SELECT timestamp, status, items_count, error_msg FROM crawler_logs ORDER BY timestamp DESC LIMIT 10",
                    conn)
                conn.close()

                if not df_logs.empty:
                    # 格式化时间显示
                    df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')


                    # 样式处理：成功绿，失败红
                    def style_status(row):
                        color = 'background-color: #2ecc7122; color: #2ecc71' if row[
                                                                                     'status'] == 'Success' else 'background-color: #e74c3c22; color: #e74c3c'
                        return [color] * len(row)


                    st.dataframe(
                        df_logs.style.apply(style_status, axis=1),
                        column_config={
                            "timestamp": "运行时间",
                            "status": "状态",
                            "items_count": "抓取数量",
                            "error_msg": "错误详情"
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                    # 运行统计小组件
                    success_count = len(df_logs[df_logs['status'] == 'Success'])
                    st.caption(f"📊 当前运行统计：成功 {success_count} / 总计 {len(df_logs)}")
                else:
                    st.info("💡 尚无运行记录，请点击上方按钮启动第一次同步。")
            except Exception as e:
                st.error(f"无法读取日志表: {e}")

        else:
            st.error("🔒 权限不足：非管理员无法访问系统管理模块。")

else:
    # 登录拦截
    st.warning("⚠️ 请先登录系统（或检查 dev_tools 设置以绕过登录）")
    if st.button("尝试默认登录"):
        st.session_state['username'] = "Admin_Tester"
        st.session_state['role'] = "admin"
        st.rerun()