"""
历史记录页
"""
import streamlit as st
from database.init import init_database as _init_db
from database.operations import get_user_sessions, get_candidate_names, get_user_balance

st.set_page_config(page_title="历史记录", page_icon="📋", layout="wide")

# ── 注入新中式主题 ──
from ui.theme import apply_theme, render_topnav
apply_theme()

# 移除左侧栏（该页不需要）
st.markdown("""
<style>
section[data-testid="stSidebar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

if 'supabase' not in st.session_state:
    st.session_state.supabase = _init_db()
supabase = st.session_state.supabase

# 从 URL 参数恢复登录
if not st.session_state.get('user_id'):
    p = st.query_params
    if "uid" in p and "email" in p:
        st.session_state.user_id = p["uid"]
        st.session_state.user_email = p["email"]

# 已登录但 URL 参数缺失 → 补写（刷新后保持登录）
if st.session_state.get('user_id'):
    if "uid" not in st.query_params:
        st.query_params["uid"] = st.session_state.user_id
    if "email" not in st.query_params:
        st.query_params["email"] = st.session_state.user_email

if not st.session_state.get('user_id'):
    st.warning("请先登录"); st.page_link("app.py", label="去登录", icon="🔑"); st.stop()

balance = get_user_balance(supabase, st.session_state.user_id)
if render_topnav("history", balance, st.session_state.user_email):
    st.session_state.remembered_email = st.session_state.user_email
    st.session_state.user_id = None; st.session_state.user_email = None
    st.query_params.clear(); st.switch_page("app.py")

st.markdown(
    "<h3 style='font-family:\"Noto Serif SC\",serif;color:#2C2C2C;margin:6px 0 12px;'>"
    "📋 取名历史记录</h3>", unsafe_allow_html=True)

_scol, _fcol = st.columns([4, 1])
with _scol:
    search = st.text_input("🔍 搜索姓氏或名字...", label_visibility="collapsed",
                           placeholder="搜索姓氏或名字...")
with _fcol:
    show_fav = st.checkbox("⭐ 仅看收藏")

sessions = get_user_sessions(supabase, st.session_state.user_id)
if not sessions:
    st.info("还没有取名记录"); st.stop()

st.caption(f"共 {len(sessions)} 条")
for s in sessions:
    sid = s['session_id']
    surname = s.get('surname', '')
    created = (s.get('created_at') or '')[:16]
    gender = s.get('gender', '')
    name_len = s.get('name_length', '')
    birth = (s.get('birth_date') or '')[:10]

    if search and search not in surname:
        continue

    names = get_candidate_names(supabase, sid)
    if show_fav:
        names = [n for n in names if n.get('is_favorite')]
    if show_fav and not names:
        continue

    # ── 标签：时间 | 性别 | 姓氏 ──
    gender_icon = "👦" if gender == "男孩" else "👧" if gender else ""
    gender_label = f"{gender_icon} {gender}" if gender else ""
    label = f"{created}  |  {gender_label}  |  {surname}姓"

    with st.expander(label):
        for n in names:
            fav = n.get('is_favorite', False)
            c1, c2 = st.columns([5, 1])
            full = n.get('full_name', n.get('name_text',''))
            c1.markdown(
                f"<span class='gn-name' style='font-size:17px;'>{full}</span>"
                f"&nbsp;&nbsp;<span class='gn-tag gn-tag-gray'>评分 {n.get('score','')}</span>"
                f"&nbsp;{n.get('meaning','')}", unsafe_allow_html=True)
            if c2.button("⭐" if fav else "☆", key=f"fav_{sid}_{n.get('id',0)}",
                         help="收藏 / 取消收藏"):
                supabase.table("candidate_names") \
                    .update({"is_favorite": not fav}) \
                    .eq("id", n['id']).execute()
                st.rerun()
