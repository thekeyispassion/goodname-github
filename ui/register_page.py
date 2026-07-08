"""
注册页面

用户输入邮箱+密码注册。
"""
import streamlit as st


def render_register_page(supabase):
    st.markdown("# 📛 取名大师")
    st.markdown("## 注册")
    st.markdown("---")

    email = st.text_input("邮箱", key="reg_email")
    password = st.text_input("密码", type="password", key="reg_password",
                             help="至少6位")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("注册", type="primary", use_container_width=True):
            if not email or not password:
                st.error("❌ 请填写邮箱和密码")
                return
            if len(password) < 6:
                st.error("❌ 密码至少6位")
                return

            try:
                result = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                })

                if result.user:
                    st.success("✅ 注册成功！请登录。")
                    st.session_state.auth_page = "login"
                    st.rerun()

            except Exception as e:
                st.error(f"❌ 注册失败：{e}")

    with col2:
        if st.button("已有账号？去登录", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()
