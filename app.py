import streamlit as st
import database as db
import engine, config, crawler, dev_tools
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="AI 内存决策终端", layout="wide", page_icon="📈")
db.init_db()
dev_tools.enable_admin_bypass() 
device, d_name = engine.get_device()

# 高级 UI 样式
st.markdown("""
<style>
    .metric-card { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid #00FF00; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
    .price-val { color: #00FF00; font-size: 32px; font-weight: bold; margin: 0; }
    .status-success { color: #2ecc71; font-weight: bold; }
    .status-failed { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if st.session_state.get('username'):
    with st.sidebar:
        st.title("🛡️ 决策终端")
        st.write(f"用户: {st.session_state['username']} ({st.session_state['role']})")
        dev_tools.show_debug_sidebar()
        st.info("💡 提示：数据现已由 GitHub Actions 每天中午 12 点自动进行全网真实采集。")

    t_data, t_admin = st.tabs(["📊 实时大盘与预测", "⚙️ 系统管理日志"])

    with t_data:
        st.title("🎯 内存价格 AI 深度决策系统")
        st.markdown("基于真实全网电商价格抓取 · 采用 PyTorch 神经网络预测趋势")
        
        c1, c2, c3 = st.columns(3)
        sb = c1.multiselect("选择监控品牌", list(config.BRAND_WEIGHTS.keys()), default=["海力士"])
        ss = c2.selectbox("选择规格", list(config.BASE_PRICES.keys()))
        sp = c3.selectbox("数据源平台", config.PLATFORMS)

        st.divider()

        if st.button("🤖 调取真实数据并执行 AI 预测", type="primary", use_container_width=True):
            fig = go.Figure()
            cols = st.columns(len(sb))
            
            for i, b in enumerate(sb):
                df_h = db.get_real_data(b, ss, sp)
                
                if not df_h.empty:
                    # --- 核心 UI 优化：计算价格涨跌幅指标 ---
                    current_price = df_h['Price'].iloc[-1]
                    price_diff = 0
                    if len(df_h) > 1:
                        price_diff = current_price - df_h['Price'].iloc[-2]
                    
                    with cols[i]:
                        st.markdown(f"### {b}")
                        # 使用 Streamlit 原生 KPI 组件展示
                        st.metric(label="当前现货全网中位价", value=f"¥ {current_price:.2f}", delta=f"{price_diff:.2f} (较前一日)")
                        st.link_button(f"🔗 前往 {sp} 查证货源", df_h['URL'].iloc[-1], use_container_width=True)

                    # --- 核心绘图优化：无缝连接历史与预测线 ---
                    df_p, acc = engine.predict_future_prices_pytorch(df_h, f"{b}_{ss}", device)

                    # 画历史实测线
                    fig.add_trace(go.Scatter(x=df_h['Date'], y=df_h['Price'], name=f"{b}-历史实测", mode='lines+markers'))

                    if not df_p.empty and 'Date' in df_p.columns:
                        # 重点：把历史的最后一条数据，追加到预测数据的最前面，消除图表断层
                        last_real_point = df_h.iloc[[-1]].copy()
                        last_real_point = last_real_point.rename(columns={'Price': 'Pred'})
                        df_p_connected = pd.concat([last_real_point, df_p])
                        
                        fig.add_trace(go.Scatter(
                            x=df_p_connected['Date'], 
                            y=df_p_connected['Pred'], 
                            name=f"{b}-AI预测轨迹", 
                            line=dict(dash='dot', width=3),
                            mode='lines+markers'
                        ))
                        with cols[i]:
                            st.caption(f"🤖 神经网络预测信心度: {acc:.1f}%")

            # 优化图表外观
            fig.update_layout(hovermode="x unified", title="📈 历史走势与未来 7 天预测", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    with t_admin:
        if st.session_state['role'] == 'admin':
            st.header("⚙️ 终端管理控制台")
            col_ctrl, col_info = st.columns([1, 2])
            with col_ctrl:
                st.subheader("🚀 手动强刷数据")
                st.caption("提示：云端每天会自动抓取，非必要无需手动强刷。")
                if st.button("🕸️ 强制唤醒爬虫抓取现价", use_container_width=True):
                    with st.spinner("正在从电商平台实时拉取数据 (需时约数十秒)..."):
                        crawler.spider.run_sync()
                        st.success("最新真实行情拉取完毕！")
                        st.rerun() 

            with col_info:
                st.subheader("🛡️ 云端爬虫运行日志")
                try:
                    conn = sqlite3.connect('memory_market.db')
                    df_logs = pd.read_sql_query("SELECT timestamp, status, items_count, error_msg FROM crawler_logs ORDER BY timestamp DESC LIMIT 10", conn)
                    conn.close()
                    if not df_logs.empty:
                        def style_status(row):
                            color = 'background-color: #2ecc7122; color: #2ecc71' if row['status'] == 'Success' else 'background-color: #e74c3c22; color: #e74c3c'
                            return [color] * len(row)
                        st.dataframe(df_logs.style.apply(style_status, axis=1), use_container_width=True, hide_index=True)
                except:
                    st.error("日志读取失败")
