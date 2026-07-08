"""
历史记录页
"""
import streamlit as st
from database.init import init_database as _init_db
from database.operations import get_user_sessions, get_candidate_names, get_user_balance

st.set_page_config(page_title="历史记录", page_icon="📋", layout="wide")

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
cols = st.columns([2, 1, 1, 2, 1, 1])
with cols[0]: st.markdown("### 📛 智能取名系统")
with cols[1]: st.page_link("pages/1_取名主页.py", label="取名主页")
with cols[2]: st.markdown("##### ✅ 历史记录")
with cols[3]: st.markdown(f"<h4 style='text-align:right'>💰 余额：{balance}次</h4>", unsafe_allow_html=True)
with cols[4]: st.page_link("pages/3_个人中心.py", label="👤 个人中心")
with cols[5]:
    if st.button("🚪 退出"):
        st.session_state.remembered_email = st.session_state.user_email
        st.session_state.user_id = None; st.session_state.user_email = None
        st.query_params.clear(); st.switch_page("app.py")
st.markdown("---")

st.markdown("## 📋 取名历史记录")
search = st.text_input("🔍 搜索姓氏或名字...")
show_fav = st.checkbox("⭐ 仅看收藏")

sessions = get_user_sessions(supabase, st.session_state.user_id)
if not sessions:
    st.info("还没有取名记录"); st.stop()

st.caption(f"共 {len(sessions)} 条")
for s in sessions:
    sid = s['session_id']; surname = s.get('surname','')
    created = (s.get('created_at') or '')[:16]
    status = "✅" if s.get('is_satisfied') else "⏳"
    gender_icon = "👦" if s.get('gender')=="男孩" else "👧"
    if search and search not in surname: continue
    names = get_candidate_names(supabase, sid)
    if show_fav: names = [n for n in names if n.get('is_favorite')]
    if show_fav and not names: continue
    preview = " · ".join([n.get('name_text','') for n in names[:3]])
    with st.expander(f"{status} {created}  {gender_icon} {surname}姓  {preview}"):
        for n in names:
            fav = n.get('is_favorite', False)
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"- {n.get('full_name',n.get('name_text',''))}（评分{n.get('score','')}）{n.get('meaning','')}")
            if c2.button("⭐" if fav else "☆", key=f"fav_{sid}_{n.get('id',0)}"):
                supabase.table("candidate_names").update({"is_favorite": not fav}).eq("id", n['id']).execute()
                st.rerun()
