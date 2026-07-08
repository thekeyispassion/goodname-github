"""
登录页面

用户输入邮箱+密码登录。
"""
import streamlit as st


def render_login_page(supabase):
    st.markdown("# 📛 取名大师")
    st.markdown("## 登录")
    st.markdown("---")

    email = st.text_input("邮箱", key="login_email")
    password = st.text_input("密码", type="password", key="login_password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("登录", type="primary", use_container_width=True):
            if not email or not password:
                st.error("❌ 请填写邮箱和密码")
                return

            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user_id = result.user.id
                st.session_state.user_email = result.user.email
                st.success(f"✅ 欢迎回来！")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 登录失败：{e}")

    with col2:
        if st.button("没有账号？去注册", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()
