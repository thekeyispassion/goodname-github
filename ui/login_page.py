"""
登录页面（v2.0 含记住密码）
"""
import streamlit as st


def render_login_page(supabase):
    st.markdown("# 📛 智能取名系统")
    st.markdown("## 登录")
    st.markdown("---")

    # 如果之前勾选了"记住我"退出，自动填充邮箱
    remembered_email = st.session_state.get("remembered_email", "")
    email = st.text_input("邮箱", value=remembered_email or None, key="login_email")
    password = st.text_input("密码", type="password", key="login_password")

    col_rem, _ = st.columns([1, 3])
    with col_rem:
        remember = st.checkbox("记住我", value=True,
                               help="勾选后刷新页面不会丢失登录状态")

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
                # 清除记住的邮箱（已登录，不再需要）
                if "remembered_email" in st.session_state:
                    del st.session_state.remembered_email

                # ✅ 记住我：把用户信息写入 URL 参数，刷新后不丢失
                if remember:
                    st.query_params["uid"] = result.user.id
                    st.query_params["email"] = result.user.email
                else:
                    # 不记住：清除 URL 参数
                    st.query_params.clear()

                st.success("✅ 登录成功！")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 登录失败：{e}")

    with col2:
        if st.button("没有账号？去注册", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()

    # 测试账号登录（DEV_MODE 走这个）
    st.markdown("---")
    st.markdown("##### 🔧 测试模式")
    test_email = "test@test.com"
    test_pwd = "Test1234"
    st.caption(f"账号：{test_email} / 密码：{test_pwd}（自动注册）")
    if st.button("⚡ 测试账号快速登录", use_container_width=True):
        # 尝试登录，失败则自动注册
        try:
            result = supabase.auth.sign_in_with_password({
                "email": test_email, "password": test_pwd
            })
        except Exception:
            try:
                supabase.auth.sign_up({"email": test_email, "password": test_pwd})
                result = supabase.auth.sign_in_with_password({
                    "email": test_email, "password": test_pwd
                })
            except Exception as e2:
                st.error(f"测试账号登录失败：{e2}")
                st.stop()

        st.session_state.user_id = result.user.id
        st.session_state.user_email = result.user.email
        st.query_params["uid"] = result.user.id
        st.query_params["email"] = result.user.email
        st.rerun()
