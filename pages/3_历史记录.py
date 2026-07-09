"""
历史记录页
"""
import streamlit as st
from database.init import init_database as _init_db
from database.operations import get_user_sessions, get_candidate_names, get_user_balance, save_user_rating, save_user_note

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

# 从 URL 参数恢复 Supabase 认证（刷新后 RLS 需要 auth.uid()）
_atok = st.query_params.get("_atok")
_rtok = st.query_params.get("_rtok")
if _atok:
    try:
        supabase.auth.set_session(_atok, _rtok)
    except Exception:
        pass

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

def _rating_badge(rating):
    """返回用户评分的徽章 HTML（空字符串表示未评分）。"""
    if rating and int(rating) > 0:
        r = int(rating)
        return f"<span class='gn-tag' style='background:#FBF3E0;'>{'⭐'*r} {r}分</span>"
    return ""

_scol, _fcol, _rcol = st.columns([3, 1, 1.3])
with _scol:
    search = st.text_input("🔍 搜索姓氏或名字...", label_visibility="collapsed",
                           placeholder="搜索姓氏或名字...")
with _fcol:
    show_fav = st.checkbox("⭐ 收藏", key="history_show_fav")
with _rcol:
    rating_filter = st.selectbox(
        "评分", ["全部", "⭐ 4星以上", "⭐ 3星以上", "⭐ 2星以上", "⭐ 未评分"],
        index=0, label_visibility="collapsed",
        key="history_rating_filter"
    )

sessions = get_user_sessions(supabase, st.session_state.user_id)
if not sessions:
    st.info("还没有取名记录"); st.stop()

# 展开状态记忆：点收藏按钮后 expander 不折叠
if 'history_expanded' not in st.session_state:
    st.session_state.history_expanded = {}

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

    # 收藏筛选（独立）
    if show_fav:
        names = [n for n in names if n.get('is_favorite')]

    # 评分筛选（独立）——可与收藏叠加
    if rating_filter == "⭐ 4星以上":
        names = [n for n in names if (n.get('user_rating') or 0) >= 4]
    elif rating_filter == "⭐ 3星以上":
        names = [n for n in names if (n.get('user_rating') or 0) >= 3]
    elif rating_filter == "⭐ 2星以上":
        names = [n for n in names if (n.get('user_rating') or 0) >= 2]
    elif rating_filter == "⭐ 未评分":
        names = [n for n in names if n.get('user_rating') is None]

    if not names:
        continue

    # ── 会话级标签：时间 | 性别 | 姓氏 ──
    gender_icon = "👦" if gender == "男孩" else "👧" if gender else ""
    gender_label = f"{gender_icon} {gender}" if gender else ""
    label = f"{created}  |  {gender_label}  |  {surname}姓"

    # 记住展开状态
    if sid not in st.session_state.history_expanded:
        st.session_state.history_expanded[sid] = False
    if st.session_state.get('_fav_just_clicked'):
        st.session_state.history_expanded[sid] = True

    with st.expander(label, expanded=st.session_state.history_expanded[sid]):
        st.session_state.history_expanded[sid] = True
        for n in names:
            name_id = n.get('id')
            full = n.get('full_name', n.get('name_text', ''))
            fav = n.get('is_favorite', False)
            # 每个名字一个可展开标签
            # 标签行：名字 + AI评分 + 用户评分徽章
            rating_html = _rating_badge(n.get('user_rating'))
            user_stars = f" {'⭐' * (n.get('user_rating') or 0)}" if n.get('user_rating') else ""
            fav_mark = " ⭐收藏" if fav else ""
            name_label = f"{full}  {n.get('score','')}分{user_stars}{fav_mark}"

            with st.expander(name_label, expanded=False):
                # ── 详细信息 ──
                if n.get('meaning', ''):
                    st.markdown(f"📖 *{n.get('meaning','')}*")
                if n.get('cultural_ref', ''):
                    st.markdown(f"📚 {n.get('cultural_ref','')}")
                wuxing = n.get('wuxing', '')
                sound = n.get('sound_rhythm', '')
                if wuxing or sound:
                    tags = ""
                    if wuxing: tags += f"<span class='gn-tag'>🔥 五行：{wuxing}</span>"
                    if sound: tags += f"<span class='gn-tag gn-tag-gray'>🎵 {sound}</span>"
                    st.markdown(tags, unsafe_allow_html=True)

                # ── 收藏按钮 ──
                if st.button("⭐ 取消收藏" if fav else "☆ 收藏", key=f"fav_{sid}_{n.get('id',0)}",
                             help="收藏 / 取消收藏"):
                    supabase.table("candidate_names") \
                        .update({"is_favorite": not fav}) \
                        .eq("id", n['id']).execute()
                    st.session_state._fav_just_clicked = True
                    st.session_state.history_expanded[sid] = True
                    st.rerun()

                # ── 用户评分 + 备注 ──
                if name_id:
                    cur_rating = n.get('user_rating') or 0
                    cur_note = n.get('user_note', '') or ''
                    sc1, sc2, sc3, sc4, sc5, nc = st.columns([0.6, 0.6, 0.6, 0.6, 0.6, 5])
                    for s_idx, s_col in enumerate([sc1, sc2, sc3, sc4, sc5]):
                        with s_col:
                            filled = s_idx < cur_rating
                            lbl = "★" if filled else "☆"
                            if st.button(lbl, key=f"hist_star_{name_id}_{s_idx}",
                                         help=f"{s_idx+1} 星"):
                                save_user_rating(supabase, name_id, s_idx + 1)
                                n['user_rating'] = s_idx + 1
                                st.session_state.history_expanded[sid] = True
                                st.rerun()
                    with nc:
                        new_note = st.text_input(
                            "备注", value=cur_note,
                            key=f"hist_note_{name_id}",
                            placeholder="写下你的评价…",
                            label_visibility="collapsed"
                        )
                        if new_note != cur_note:
                            save_user_note(supabase, name_id, new_note)
                            n['user_note'] = new_note
                            st.rerun()

# 清理收藏点击标记
if st.session_state.get('_fav_just_clicked'):
    st.session_state._fav_just_clicked = False
