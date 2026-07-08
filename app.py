"""
取名大师 v2.0 - 登录/注册页（多页面入口）

Streamlit 原生多页面结构：
  app.py                 → 登录/注册
  pages/1_取名主页.py     → 取名功能
  pages/2_历史记录.py     → 历史记录
  pages/3_个人中心.py     → 个人中心/充值/修改密码
"""
import os
import streamlit as st
from database.init import init_database
from database.operations import get_user_balance

st.set_page_config(page_title="智能取名系统 - 登录", page_icon="📛", layout="centered")

# ── 注入新中式主题 ──
from ui.theme import apply_theme
apply_theme()

# 移除 Streamlit 自动生成的左侧导航栏（Pages 菜单）
st.markdown("""
<style>
nav[data-testid="stSidebarNav"] {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

if 'supabase' not in st.session_state:
    st.session_state.supabase = init_database()
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'auth_page' not in st.session_state:
    st.session_state.auth_page = "login"

supabase = st.session_state.supabase

if supabase is None:
    st.error("⚠️ Supabase 未配置，请在 .env 中设置 SUPABASE_URL 和 SUPABASE_KEY")
    st.stop()

# 从 URL 参数恢复登录
if not st.session_state.user_id:
    params = st.query_params
    if "uid" in params and "email" in params:
        st.session_state.user_id = params["uid"]
        st.session_state.user_email = params["email"]

# 已登录但 URL 参数缺失 → 补写（刷新后保持登录）
if st.session_state.user_id:
    if "uid" not in st.query_params:
        st.query_params["uid"] = st.session_state.user_id
    if "email" not in st.query_params:
        st.query_params["email"] = st.session_state.user_email

# 已登录 → 跳转取名主页
if st.session_state.user_id:
    # 登录成功，清除登录页 widget 缓存
    for k in ['login_email', 'login_password', 'login_username',
              'reg_email', 'reg_password', 'reg_confirm', 'reg_username']:
        if k in st.session_state: del st.session_state[k]
    st.switch_page("pages/1_取名主页.py")

# 未登录 → 显示登录/注册
dev_mode = os.environ.get("DEV_MODE", "").lower()
if dev_mode in ("true", "1"):
    st.session_state.user_id = "dev-user"
    st.session_state.user_email = "dev@dev.com"
    st.switch_page("pages/1_取名主页.py")

if st.session_state.auth_page == "register":
    from ui.register_page import render_register_page
    render_register_page(supabase)
else:
    from ui.login_page import render_login_page
    render_login_page(supabase)
