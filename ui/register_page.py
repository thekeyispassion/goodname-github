"""
注册页面（v2.0 - 单卡片包裹所有元素）
"""
import re
import streamlit as st


def _validate_password(pwd: str) -> tuple:
    errors = []
    if len(pwd) < 8:
        errors.append("密码至少8位")
    if not re.search(r'[a-z]', pwd):
        errors.append("需包含小写字母")
    if not re.search(r'[A-Z]', pwd):
        errors.append("需包含大写字母")
    if not re.search(r'\d', pwd):
        errors.append("需包含数字")
    return (len(errors) == 0, "；".join(errors))


def _password_strength(pwd: str) -> str:
    score = 0
    if len(pwd) >= 8: score += 1
    if re.search(r'[a-z]', pwd): score += 1
    if re.search(r'[A-Z]', pwd): score += 1
    if re.search(r'\d', pwd): score += 1
    if re.search(r'[!@#$%^&*]', pwd): score += 1
    if score <= 2: return "弱", "#E53935"
    if score <= 3: return "中", "#FB8C00"
    return "强", "#43A047"


def render_register_page(supabase):
    with st.container():
        st.markdown("""
        <div class="gn-auth-wrap">
          <div class="gn-auth-card">
            <div class="gn-auth-logo">
              <span class="gn-seal">印</span>
            </div>
            <h2 style="text-align:center;color:#2C2C2C;margin-top:10px;">智能取名系统</h2>
            <p style="text-align:center;color:#8C8C8C;font-size:14px;margin-bottom:20px;">创建新账户</p>
        """, unsafe_allow_html=True)

        email = st.text_input("邮箱", key="reg_email", placeholder="请输入邮箱地址")
        password = st.text_input("密码", type="password", key="reg_password",
                                placeholder="请设置密码")
        confirm = st.text_input("确认密码", type="password", key="reg_confirm",
                               placeholder="请再次输入密码")

        if password:
            level, color = _password_strength(password)
            st.markdown(f"密码强度：<span style='color:{color};font-weight:bold'>{level}</span>",
                        unsafe_allow_html=True)
            st.progress(min(len(password) / 12, 1.0))

        if st.button("注 册", type="primary", use_container_width=True):
            if not email or not password or not confirm:
                st.error("❌ 请填写所有字段"); return
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                st.error("❌ 邮箱格式不正确"); return
            ok, msg = _validate_password(password)
            if not ok:
                st.error(f"❌ {msg}"); return
            if password != confirm:
                st.error("❌ 两次密码不一致"); return
            try:
                result = supabase.auth.sign_up({"email": email, "password": password})
                if result.user:
                    st.success("✅ 注册成功！请登录。")
                    st.session_state.auth_page = "login"; st.rerun()
            except Exception as e:
                err = str(e)
                if "already" in err.lower():
                    st.error("❌ 该邮箱已注册")
                elif "database error" in err.lower():
                    st.error("❌ 注册失败：数据库触发器冲突。")
                else:
                    st.error(f"❌ 注册失败：{e}")

        if st.button("已有账号？返回登录", use_container_width=True):
            st.session_state.auth_page = "login"; st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)
