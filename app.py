"""
取名大师 - 主入口（难度2）

改动说明：
- 难度1：直接显示取名功能
- 难度2：先判断登录态 → 未登录显示登录/注册页 → 已登录才显示取名功能

运行：streamlit run app.py
"""
import os
import streamlit as st
from database.init import init_database
from database.operations import (
    create_session,
    save_message,
    save_names,
)
from llm.client import call_deepseek
from llm.prompt_builder import build_initial_prompt, build_refine_prompt, _get_name_char_count
from utils.parser import parse_ai_response
from ui.sidebar import render_sidebar
from ui.chat_area import render_chat_area
from ui.login_page import render_login_page
from ui.register_page import render_register_page
from history_page import render_history_page


# ════════════════════════════════════════════════════════════
# 第0步：辅助函数
# ════════════════════════════════════════════════════════════

def _get_expected_chars(user_input):
    surname = user_input.get('surname', '')
    return _get_name_char_count(user_input.get('name_length', ''), surname)


def _validate_name_lengths(names, user_input):
    expected = _get_expected_chars(user_input)
    if expected is None:
        return names

    validated = []
    for name in names:
        name_text = name.get('name', '')
        if name_text and len(name_text) != expected:
            print(f"⚠️ 名字「{name.get('full_name', name_text)}」字数{len(name_text)}!=期望{expected}")
            name['_length_mismatch'] = True
        else:
            name['_length_mismatch'] = False
        validated.append(name)
    return validated


# ════════════════════════════════════════════════════════════
# 第1步：页面配置
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="取名大师",
    page_icon="📛",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ════════════════════════════════════════════════════════════
# 第2步：初始化 session_state
# ════════════════════════════════════════════════════════════

# ---- Supabase 客户端（全局共用） ----
if 'supabase' not in st.session_state:
    st.session_state.supabase = init_database()

# ---- 登录态 ----
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'auth_page' not in st.session_state:
    st.session_state.auth_page = "login"  # "login" 或 "register"

# ---- 页面路由 ----
if 'page' not in st.session_state:
    st.session_state.page = "home"  # "home" 或 "history"

# ---- 难度1原有的状态变量 ----
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = st.session_state.supabase  # 兼容旧代码用 conn
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'round_number' not in st.session_state:
    st.session_state.round_number = 0
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'info_submitted' not in st.session_state:
    st.session_state.info_submitted = False
if 'need_process' not in st.session_state:
    st.session_state.need_process = False
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'user_input' not in st.session_state:
    st.session_state.user_input = {}


# ════════════════════════════════════════════════════════════
# 第3步：登录态判断（★ 难度2新增）
# ════════════════════════════════════════════════════════════

supabase = st.session_state.supabase

# Supabase 未配置时给出提示
if supabase is None:
    st.error("⚠️ Supabase 未配置")
    st.markdown("""
    请在 `.env` 文件中设置：
    ```
    SUPABASE_URL=https://你的项目.supabase.co
    SUPABASE_KEY=你的anon-key
    ```
    然后在 Supabase 后台 SQL Editor 中运行 `database/supabase_schema.sql` 建表。
    """)
    st.stop()

# 未登录 → 拦截，显示登录/注册页
if not st.session_state.user_id:
    # ★ 开发模式：跳过登录，直接进入（.env 设 DEV_MODE=true 即可）
    if os.environ.get("DEV_MODE", "").lower() == "true" or os.environ.get("DEV_MODE", "") == "1":
        st.session_state.user_id = "dev-user-00000000-0000-0000-0000-000000000000"
        st.session_state.user_email = "dev@dev.com"
    else:
        if st.session_state.auth_page == "register":
            render_register_page(supabase)
        else:
            render_login_page(supabase)
        st.stop()  # ← 关键！不往后执行，取名功能被保护


# ════════════════════════════════════════════════════════════
# 第4步：页面路由（已登录用户）
# ════════════════════════════════════════════════════════════

# 历史记录页面
if st.session_state.page == "history":
    render_history_page(supabase)
    # 返回首页按钮
    if st.button("← 返回首页"):
        st.session_state.page = "home"
        st.rerun()
    st.stop()


# ════════════════════════════════════════════════════════════
# 第5步：取名主页面（难度1原有功能）
# ════════════════════════════════════════════════════════════

# ===== 左侧：侧边栏 =====
with st.sidebar:
    st.markdown("# 📛 取名大师")

    # ★ 导航按钮
    if st.button("📋 历史记录", use_container_width=True):
        st.session_state.page = "history"
        st.rerun()
    if st.button("🚪 退出登录", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.info_submitted = False
        st.rerun()

    st.markdown("---")
    st.caption(f"当前用户：{st.session_state.user_email}")

    # 信息采集面板
    if st.session_state.info_submitted:
        info = st.session_state.user_input
        st.info(
            f"👤 {info.get('surname', '')}姓 {info.get('gender', '')} "
            f"{' | ' + info.get('name_length', '') if info.get('name_length') else ''}"
        )
        with st.expander("📝 查看/修改信息"):
            render_sidebar()
    else:
        render_sidebar()


# ===== 右侧：主区域 =====
if not st.session_state.info_submitted:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding-top: 80px;">
            <h1 style="font-size: 3em;">📛</h1>
            <h1>取名大师</h1>
            <p style="font-size: 18px; color: #666;">
                请在左侧填写信息，点击「开始取名」
            </p>
            <p style="font-size: 14px; color: #999;">
                基于 DeepSeek AI 智能生成寓意美好的中文名字
            </p>
        </div>
        """, unsafe_allow_html=True)
else:
    render_chat_area()


# ════════════════════════════════════════════════════════════
# 第6步：业务逻辑（和难度1基本一致，调的是 Supabase 版本 operations）
# ════════════════════════════════════════════════════════════

# ——— 情况A：首次提交表单 ———
if st.session_state.info_submitted and st.session_state.session_id is None:
    st.session_state.is_processing = True
    supabase = st.session_state.supabase

    with st.spinner("🤔 正在根据信息取名中..."):

        session_id = create_session(
            supabase,
            st.session_state.user_input,
            user_id=st.session_state.user_id  # ★ 传入当前用户ID
        )
        st.session_state.session_id = session_id
        st.session_state.round_number = 1

        messages = build_initial_prompt(st.session_state.user_input)
        user_content = messages[-1]["content"]
        save_message(supabase, session_id, "user", user_content, round_number=1)
        response = call_deepseek(messages)

        if response:
            names = parse_ai_response(response)
            if names:
                names = _validate_name_lengths(names, st.session_state.user_input)

            save_message(supabase, session_id, "assistant", response, round_number=1)
            if names:
                save_names(supabase, session_id, names, round_number=1)

            display_content = names if names else response
            st.session_state.messages.append({
                "role": "assistant",
                "content": display_content
            })
        else:
            st.error("❌ AI 暂时无法响应，请稍后重试")
            st.session_state.messages.append({
                "role": "assistant",
                "content": "抱歉，无法连接到 AI 服务。请检查 API Key 和网络。"
            })

        st.session_state.is_processing = False
        st.rerun()


# ——— 情况B：用户提修改意见 ———
if st.session_state.get('need_process', False):
    st.session_state.need_process = False
    st.session_state.is_processing = True
    supabase = st.session_state.supabase
    session_id = st.session_state.session_id

    st.session_state.round_number += 1
    round_num = st.session_state.round_number

    if st.session_state.messages:
        user_feedback = st.session_state.messages[-1]["content"]
    else:
        user_feedback = ""

    with st.spinner(f"🔄 第 {round_num} 轮优化中..."):

        history = st.session_state.messages[:-1]
        messages = build_refine_prompt(
            st.session_state.user_input,
            history,
            user_feedback
        )

        save_message(supabase, session_id, "user", user_feedback, round_number=round_num)
        response = call_deepseek(messages)

        if response:
            names = parse_ai_response(response)
            if names:
                names = _validate_name_lengths(names, st.session_state.user_input)

            save_message(supabase, session_id, "assistant", response, round_number=round_num)
            if names:
                save_names(supabase, session_id, names, round_number=round_num)

            display_content = names if names else response
            st.session_state.messages.append({
                "role": "assistant",
                "content": display_content
            })
        else:
            st.error("❌ AI 暂时无法响应，请稍后重试")
            st.session_state.messages.append({
                "role": "assistant",
                "content": "抱歉，AI 服务暂时不可用，请稍后再试。"
            })

        st.session_state.is_processing = False
        st.rerun()
