"""
登录页面（v2.0 - 单卡片包裹所有元素）
"""
import streamlit as st


def _clean_old_session():
    for k in ['messages', 'round_number', 'session_id',
              'info_submitted', 'need_process', 'is_processing',
              'user_input', 'profile_page',
              'eval_result', 'eval_done_name', 'eval_processing', 'eval_name']:
        if k in st.session_state:
            del st.session_state[k]


def render_login_page(supabase):
    # 卡片包裹所有内容的容器
    with st.container():
        # 开卡片 + Logo + 标题
        st.markdown("""
        <div class="gn-auth-wrap">
          <div class="gn-auth-card">
            <div class="gn-auth-logo">
              <span class="gn-seal">印</span>
            </div>
            <h2 style="text-align:center;color:#2C2C2C;margin-top:10px;">智能取名系统</h2>
            <p style="text-align:center;color:#8C8C8C;font-size:14px;margin-bottom:20px;">登录您的账户</p>
        """, unsafe_allow_html=True)

        remembered_email = st.session_state.get("remembered_email", "")
        email = st.text_input("邮箱", value=remembered_email or None,
                              key="login_email", placeholder="请输入邮箱地址")
        password = st.text_input("密码", type="password",
                                 key="login_password", placeholder="请输入密码")

        col_rem, _ = st.columns([1, 3])
        with col_rem:
            remember = st.checkbox("记住我", value=True,
                                   help="勾选后刷新页面不会丢失登录状态")

        col1, col2 = st.columns(2)
        with col1:
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
                    # 保存认证 token 到 URL 参数（刷新后恢复 RLS）
                    if result.session:
                        st.query_params["_atok"] = result.session.access_token
                        st.query_params["_rtok"] = result.session.refresh_token
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

        with col2:
            if st.button("没有账号？去注册", use_container_width=True):
                st.session_state.auth_page = "register"
                st.rerun()

        # 测试账号区
        st.markdown("<hr style='border-color:#E5E0D8;margin:16px 0;'>",
                    unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#8C8C8C;font-size:13px;'>"
                    "🔧 测试模式</p>", unsafe_allow_html=True)
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
            if result.session:
                st.query_params["_atok"] = result.session.access_token
                st.query_params["_rtok"] = result.session.refresh_token
            st.query_params["uid"] = result.user.id
            st.query_params["email"] = result.user.email
            st.rerun()

        # 关卡片
        st.markdown("</div></div>", unsafe_allow_html=True)
