"""
登录页面（v2.0）
"""
import streamlit as st


def _clean_old_session():
    """清除上一用户留下的取名数据"""
    for k in ['messages', 'round_number', 'session_id',
              'info_submitted', 'need_process', 'is_processing',
              'user_input', 'profile_page']:
        if k in st.session_state:
            del st.session_state[k]


def render_login_page(supabase):
    st.markdown("""
    <div class="gn-auth-wrap">
      <div class="gn-auth-card">
        <div class="gn-auth-logo">
          <span class="gn-seal">印</span>
        </div>
        <h2 style="text-align:center; color:#2C2C2C; margin-top:10px;">智能取名系统</h2>
        <p style="text-align:center; color:#8C8C8C; font-size:14px; margin-bottom:24px;">登录您的账户</p>
    """, unsafe_allow_html=True)

    remembered_email = st.session_state.get("remembered_email", "")
    email = st.text_input("邮箱", value=remembered_email or None, key="login_email",
                          placeholder="请输入邮箱地址")
    password = st.text_input("密码", type="password", key="login_password",
                             placeholder="请输入密码")

    col_rem, _ = st.columns([1, 3])
    with col_rem:
        remember = st.checkbox("记住我", value=True,
                               help="勾选后刷新页面不会丢失登录状态")

    # 登录按钮：独占一行的全宽朱砂红按钮
    if st.button("登 录", type="primary", use_container_width=True):
        if not email or not password:
            st.error("❌ 请填写邮箱和密码")
            return

        try:
            result = supabase.auth.sign_in_with_password({
                "email": email, "password": password
            })
            _clean_old_session()
            st.session_state.user_id = result.user.id
            st.session_state.user_email = result.user.email
            if "remembered_email" in st.session_state:
                del st.session_state.remembered_email
            if remember:
                st.query_params["uid"] = result.user.id
                st.query_params["email"] = result.user.email
            else:
                st.query_params.clear()
            st.success("✅ 登录成功！")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 登录失败：{e}")

    # 注册引导：文字风格链接按钮（居中，点击跳注册页）
    if st.button("还没有账号？立即注册", use_container_width=True,
                 key="goto_register", type="secondary"):
        st.session_state.auth_page = "register"
        st.rerun()

    st.markdown("<hr style='border-color:#E5E0D8; margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#8C8C8C; font-size:13px;'>🔧 测试模式</p>",
                unsafe_allow_html=True)
    test_email = "test@test.com"
    test_pwd = "Test1234"
    st.caption(f"账号：{test_email} / 密码：{test_pwd}（自动注册）")
    if st.button("⚡ 测试账号快速登录", use_container_width=True):
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

        _clean_old_session()
        st.session_state.user_id = result.user.id
        st.session_state.user_email = result.user.email
        st.query_params["uid"] = result.user.id
        st.query_params["email"] = result.user.email
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
