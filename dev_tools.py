import streamlit as st


def enable_admin_bypass():
    """
    开发环境专属：强制注入管理员 Session 状态，跳过登录界面
    """
    # 检查是否已经登录，如果没有，直接强行塞入 admin 信息
    if 'username' not in st.session_state or st.session_state['username'] is None:
        st.session_state['username'] = 'admin'
        st.session_state['role'] = 'admin'
        st.session_state['pred_cache'] = {}
        # 顺便在后台打印一下，提醒你现在是调试模式
        print("🛠️  [DEV MODE] 管理员权限已自动注入")


def show_debug_sidebar():
    """
    在侧边栏显示一个调试开关，方便你在 user 和 admin 之间反复横跳
    """
    with st.sidebar:
        st.divider()
        st.subheader("🛠️ 开发工具箱")
        new_role = st.selectbox("快速切换身份", ["admin", "user", "None"])

        if st.button("🔄 立即切换"):
            if new_role == "None":
                st.session_state['username'] = None
                st.session_state['role'] = None
            else:
                st.session_state['username'] = f"test_{new_role}"
                st.session_state['role'] = new_role
            st.rerun()