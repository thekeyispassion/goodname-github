"""
注册页面（v2.0 含密码强度校验）
⚠️ 只改样式，不改变任何注册逻辑。
"""
import re
import streamlit as st
from ui.theme import PRIMARY, INK, GRAY


def _validate_password(pwd: str) -> tuple:
    """校验密码强度"""
    errors = []
    if len(pwd) < 8: errors.append("密码至少8位")
    if not re.search(r'[a-z]', pwd): errors.append("需包含小写字母")
    if not re.search(r'[A-Z]', pwd): errors.append("需包含大写字母")
    if not re.search(r'\d', pwd): errors.append("需包含数字")
    return (len(errors) == 0, "；".join(errors))


def _password_strength(pwd: str) -> str:
    """评估密码强度"""
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
    _left, center, _right = st.columns([1, 1.6, 1])
    with center:
        st.markdown(f"""
        <div style='text-align:center; margin-bottom:8px;'>
            <div style='display:inline-flex; align-items:center; justify-content:center;
                        width:56px; height:56px; border-radius:14px;
                        background:{PRIMARY}; color:#fff; font-size:30px;
                        box-shadow:0 6px 18px rgba(196,61,61,.30); margin-bottom:14px;'>印</div>
            <h2 style='margin:0; font-family:"Noto Serif SC",serif; color:{INK};'>智能取名系统</h2>
            <p style='color:{GRAY}; margin:4px 0 18px; font-size:14px;'>创建新账户</p>
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input("邮箱", key="reg_email", placeholder="请输入邮箱地址")
        password = st.text_input("密码", type="password", key="reg_password", placeholder="请设置密码")
        confirm = st.text_input("确认密码", type="password", key="reg_confirm", placeholder="请再次输入密码")

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
                    st.error("❌ 注册失败：数据库触发器冲突。请在 Supabase SQL Editor 运行 `database/fix_registration.sql` 修复。")
                else:
                    st.error(f"❌ 注册失败：{e}")

        if st.button("已有账号？返回登录", use_container_width=True,
                     key="goto_login", type="secondary"):
            st.session_state.auth_page = "login"; st.rerun()