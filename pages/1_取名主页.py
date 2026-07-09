"""
取名主页 - 多页面版
"""
import streamlit as st
from database.init import init_database as _init_db
from database.operations import (
    create_session, save_message, save_names,
    deduct_balance, get_user_balance
)
from llm.client import call_deepseek
from llm.prompt_builder import build_initial_prompt, build_refine_prompt, _get_name_char_count
from utils.parser import parse_ai_response
from ui.sidebar import render_sidebar
from ui.chat_area import render_chat_area

st.set_page_config(page_title="取名主页", page_icon="📛", layout="wide")

# ── 注入新中式主题 ──
from ui.theme import apply_theme, render_topnav
apply_theme()

# 移除 Streamlit 自动生成的左侧导航栏（Pages 菜单）
st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# 初始化 Supabase
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

# 登录检查
if not st.session_state.get('user_id'):
    st.warning("请先登录")
    st.page_link("app.py", label="去登录", icon="🔑")
    st.stop()

# ── 顶部导航 ──
balance = get_user_balance(supabase, st.session_state.user_id)
if render_topnav("home", balance, st.session_state.user_email):
    st.session_state.remembered_email = st.session_state.user_email
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.query_params.clear()
    st.switch_page("app.py")

# ── 初始化页内状态 ──
for key in ['messages', 'round_number', 'session_id', 'info_submitted',
             'need_process', 'is_processing', 'user_input']:
    if key not in st.session_state:
        if key in ('round_number',):
            st.session_state[key] = 0
        elif key in ('info_submitted', 'need_process', 'is_processing'):
            st.session_state[key] = False
        elif key == 'user_input':
            st.session_state[key] = {}
        elif key == 'session_id':
            st.session_state[key] = None
        else:
            st.session_state[key] = []

# ── 侧边栏 ──
with st.sidebar:
    if st.session_state.info_submitted:
        info = st.session_state.user_input
        st.info(f"👤 {info.get('surname','')}姓 {info.get('gender','')}"
                f"{' | '+info.get('name_length','') if info.get('name_length') else ''}")
        with st.expander("📝 查看/修改信息"):
            render_sidebar()
    else:
        render_sidebar()

# ── 主区域 ──
if not st.session_state.info_submitted:
    # 欢迎区：AI 头像（吉祥物）+ 对话气泡，引导用户填写左侧信息
    st.markdown("""
    <div style='display:flex; align-items:flex-start; justify-content:center;
                gap:16px; padding:70px 20px 0;'>
        <!-- AI 吉祥物头像 -->
        <div style='display:inline-flex; align-items:center; justify-content:center;
                    width:72px; height:72px; border-radius:50%;
                    background:linear-gradient(135deg,#C43D3D 0%,#A52F2F 100%);
                    color:#fff; font-size:38px; flex-shrink:0;
                    box-shadow:0 8px 22px rgba(196,61,61,.30);'>🦌</div>
        <!-- 对话气泡 -->
        <div style='position:relative; max-width:420px; background:#FFFFFF;
                    border:1px solid #E5E0D8; border-radius:16px; padding:16px 20px;
                    box-shadow:0 4px 16px rgba(44,44,44,.06);'>
            <span style='position:absolute; left:-8px; top:18px; width:0; height:0;
                        border-top:8px solid transparent; border-bottom:8px solid transparent;
                        border-right:10px solid #FFFFFF;'></span>
            <p style='margin:0; color:#2C2C2C; font-size:16px; line-height:1.7;'>
                你好！我是你的<strong style='color:#C43D3D;'>取名助手</strong> 🌿<br/>
                请在左侧填写宝宝信息，点击「确定 / 开始取名」，<br/>
                我将为您智能生成候选名字及完整解析。
            </p>
            <p style='margin:10px 0 0; color:#B0AAA0; font-size:13px;'>
                每次生成消耗 1 次余额
            </p>
        </div>
    </div>""", unsafe_allow_html=True)
else:
    render_chat_area()

# ── 校验辅助 ──
def _vl(names, ui):
    e = _get_name_char_count(ui.get('name_length',''), ui.get('surname',''))
    if e is None: return names
    for n in names:
        n['_length_mismatch'] = bool(n.get('name','') and len(n['name']) != e)
    return names

# ── 情况A：首次生成 ──
if st.session_state.info_submitted and st.session_state.session_id is None:
    st.session_state.is_processing = True
    uid = st.session_state.user_id
    if get_user_balance(supabase, uid) < 1:
        st.error("❌ 余额不足，请先充值")
        # 不提前设 info_submitted=False，保留页面状态让用户看到按钮
        if st.button("⚡ 去充值", type="primary"):
            st.session_state.info_submitted = False
            st.session_state.is_processing = False
            st.session_state.profile_page = "recharge"
            st.switch_page("pages/4_个人中心.py")
        st.stop()

    with st.spinner("🤔 正在取名..."):
        sid = create_session(supabase, st.session_state.user_input, uid)
        st.session_state.session_id = sid
        st.session_state.round_number = 1
        deduct_balance(supabase, uid, sid, 'generate')

        msgs = build_initial_prompt(st.session_state.user_input)
        save_message(supabase, sid, "user", msgs[-1]["content"], 1)
        resp = call_deepseek(msgs)
        if resp:
            names = parse_ai_response(resp)
            if names:
                names = _vl(names, st.session_state.user_input)
            save_message(supabase, sid, "assistant", resp, 1)
            if names:
                inserted = save_names(supabase, sid, names, 1) or []
                for i, nd in enumerate(names):
                    if i < len(inserted):
                        nd['id'] = inserted[i]['id']
            st.session_state.messages.append({"role":"assistant","content": names if names else resp})
        else:
            st.error("❌ AI 暂不可用")
            st.session_state.messages.append({"role":"assistant","content":"AI服务暂不可用。"})
        st.session_state.is_processing = False; st.rerun()

# ── 情况B：修改 ──
if st.session_state.get('need_process', False):
    st.session_state.need_process = False; st.session_state.is_processing = True
    sid = st.session_state.session_id
    st.session_state.round_number += 1
    rn = st.session_state.round_number

    uid = st.session_state.user_id
    if get_user_balance(supabase, uid) < 1:
        st.error("❌ 余额不足，请充值")
        if st.button("⚡ 去充值"):
            st.session_state.is_processing = False
            st.session_state.profile_page = "recharge"
            st.switch_page("pages/4_个人中心.py")
        st.stop()

    fb = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
    with st.spinner(f"🔄 第{rn}轮..."):
        deduct_balance(supabase, uid, sid, 'refine')
        msgs = build_refine_prompt(st.session_state.user_input, st.session_state.messages[:-1], fb)
        save_message(supabase, sid, "user", fb, rn)
        resp = call_deepseek(msgs)
        if resp:
            names = parse_ai_response(resp)
            if names: names = _vl(names, st.session_state.user_input)
            save_message(supabase, sid, "assistant", resp, rn)
            if names:
                inserted = save_names(supabase, sid, names, rn) or []
                for i, nd in enumerate(names):
                    if i < len(inserted):
                        nd['id'] = inserted[i]['id']
            st.session_state.messages.append({"role":"assistant","content": names if names else resp})
        else:
            st.error("❌ AI 暂不可用")
        st.session_state.is_processing = False; st.rerun()
