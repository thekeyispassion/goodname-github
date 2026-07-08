"""
注册页面（v2.0 含密码强度校验）
"""
import re
import streamlit as st


def _validate_password(pwd: str) -> tuple:
    """校验密码强度。返回 (是否通过, 提示)"""
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
    st.markdown("# 📛 智能取名系统")
    st.markdown("## 注册")
    st.markdown("---")

    email = st.text_input("邮箱", key="reg_email")
    password = st.text_input("密码", type="password", key="reg_password")
    confirm = st.text_input("确认密码", type="password", key="reg_confirm")

    # 实时密码强度
    if password:
        level, color = _password_strength(password)
        st.markdown(f"密码强度：<span style='color:{color};font-weight:bold'>{level}</span>",
                    unsafe_allow_html=True)
        st.progress(min(len(password) / 12, 1.0))

    if st.button("注册", type="primary", use_container_width=True):
        if not email or not password or not confirm:
            st.error("❌ 请填写所有字段")
            return

        # 邮箱格式
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            st.error("❌ 邮箱格式不正确")
            return

        # 密码强度
        ok, msg = _validate_password(password)
        if not ok:
            st.error(f"❌ {msg}")
            return

        # 密码一致性
        if password != confirm:
            st.error("❌ 两次密码不一致")
            return

        try:
            result = supabase.auth.sign_up({"email": email, "password": password})
            if result.user:
                st.success("✅ 注册成功！请登录。")
                st.session_state.auth_page = "login"
                st.rerun()
        except Exception as e:
            err = str(e)
            if "already" in err.lower():
                st.error("❌ 该邮箱已注册")
            elif "database error" in err.lower():
                st.error("❌ 注册失败：数据库触发器冲突。请在 Supabase SQL Editor 运行 `database/fix_registration.sql` 修复。")
            else:
                st.error(f"❌ 注册失败：{e}")

    if st.button("已有账号？去登录"):
        st.session_state.auth_page = "login"
        st.rerun()
