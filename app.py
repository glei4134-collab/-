import streamlit as st
import database as db
import engine, config, crawler, dev_tools
import plotly.graph_objects as go

st.set_page_config(page_title="AI 内存决策终端", layout="wide")
db.init_db()
dev_tools.enable_admin_bypass() # 🌟 开启默认管理员进入
device, d_name = engine.get_device()

# UI 样式
st.markdown("<style>.price-val { color: #00FF00; font-size: 28px; font-weight: bold; }</style>", unsafe_allow_html=True)

if st.session_state.get('username'):
    with st.sidebar:
        st.title("🛡️ 决策终端")
        st.write(f"用户: {st.session_state['username']} ({st.session_state['role']})")
        dev_tools.show_debug_sidebar()

    t_data, t_admin = st.tabs(["📊 价格趋势 (RMB)", "⚙️ 系统管理"])

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

                    # 1. 先画实测线（只要有数据就能画）
                    fig.add_trace(go.Scatter(x=df_h['Date'], y=df_h['Price'], name=f"{b}-实测"))

                    # 🌟 关键防御：检查 df_p 是否有数据，且是否包含 'Date' 列
                    if not df_p.empty and 'Date' in df_p.columns:
                        fig.add_trace(
                            go.Scatter(x=df_p['Date'], y=df_p['Pred'], name=f"{b}-预测", line=dict(dash='dot')))
                        with cols[i]:
                            st.write(f"📈 {b} 预测信心度: {acc:.1f}%")
                    else:
                        with cols[i]:
                            st.warning(f"⚠️ {b} 历史数据不足10条，AI 暂无法绘出趋势线")

                    # 展示价格卡片
                    st.markdown(f"{b} 最新价: <span class='price-val'>¥{df_h['Price'].iloc[-1]}</span>",
                                unsafe_allow_html=True)
                    st.link_button(f"🔗 查证原始网页", df_h['URL'].iloc[-1], use_container_width=True)

            st.plotly_chart(fig, use_container_width=True)

    with t_admin:
        if st.session_state['role'] == 'admin':
            if st.button("🕸️ 启动全网同步 (多样本中位数算法)"):
                with st.spinner("数据注入中..."):
                    logs = crawler.spider.run_sync()
                    st.success(f"同步完成，已更新品牌价格矩阵。")
        else: st.error("非管理员无法访问")
else:
    st.warning("请登录（或检查 dev_tools 设置）")