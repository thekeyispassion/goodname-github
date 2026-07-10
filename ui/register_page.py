"""
注册页面（v2.0 - 单卡片包裹所有元素）
"""
import re
import streamlit as st
from ui.theme import auto_error


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
        # 密码格式提示
        with st.expander("📌 密码格式要求", expanded=not bool(password)):
            st.markdown("""
            <div style='font-size:13px;color:#8C8C8C;line-height:1.8;'>
            至少 <b>8 位</b>，须包含：
            <br>• 小写字母（a-z）
            <br>• 大写字母（A-Z）
            <br>• 数字（0-9）
            </div>
            """, unsafe_allow_html=True)

        confirm = st.text_input("确认密码", type="password", key="reg_confirm",
                               placeholder="请再次输入密码")

        if password:
            level, color = _password_strength(password)
            # 实时检查各项
            checks = []
            checks.append("✅" if len(password) >= 8 else "❌")
            checks.append("✅" if re.search(r'[a-z]', password) else "❌")
            checks.append("✅" if re.search(r'[A-Z]', password) else "❌")
            checks.append("✅" if re.search(r'\d', password) else "❌")
            st.markdown(
                f"<span style='color:{color};font-weight:bold'>密码强度：{level}</span>"
                f"&nbsp;&nbsp;{checks[0]}≥8位 {checks[1]}小写 {checks[2]}大写 {checks[3]}数字",
                unsafe_allow_html=True)
            st.progress(min(len(password) / 12, 1.0))

        if st.button("注 册", type="primary", use_container_width=True):
            valid = True
            if not email or not password or not confirm:
                auto_error("请填写所有字段"); valid = False
            elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                auto_error("邮箱格式不正确"); valid = False
            else:
                ok, msg = _validate_password(password)
                if not ok:
                    auto_error(msg); valid = False
                elif password != confirm:
                    auto_error("两次密码不一致"); valid = False
            if valid:
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
