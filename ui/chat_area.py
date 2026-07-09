"""
右侧对话区域

作用：展示取名对话，包括：
1. 对话历史 - 用户说的每句话、AI给的每个回复
2. 名字卡片 - 每个候选名展示为一张信息卡（含评分、字义、五行等）
3. 输入框 - 底部固定，用户输入修改意见

和 app.py 的配合：
- app.py 调用 render_chat_area() 来渲染右侧页面
- 用户在输入框写东西 → 存入 st.session_state.messages
- 设置 need_process = True → app.py 检测到后调用 AI 优化
"""
import streamlit as st
from utils.parser import parse_ai_response
from database.operations import save_user_rating, save_user_note


def render_chat_area():
    """
    渲染右侧对话区域。

    这个函数做了两件事：
    1. 显示已有的所有对话消息（历史）
    2. 在底部放一个输入框（让用户写新消息）
    """
    st.markdown("## 💬 取名对话")
    st.markdown("---")

    # ========== 显示历史消息 ==========
    # st.session_state.get('messages', []) 从"内存仓库"中取出聊天记录
    # 如果还没有消息（第一次进来），就给一个空列表 []
    messages = st.session_state.get('messages', [])

    # enumerate 的作用：
    # 普通写法：for msg in messages → 只能拿到消息内容
    # enumerate：for msg_idx, msg in messages → 还能拿到消息序号（0,1,2...）
    # 这个序号用来给每个组件的 key 加后缀，防止名字重复报错
    for msg_idx, msg in enumerate(messages):
        role = msg["role"]      # "user" 或 "assistant"
        content = msg["content"]  # 消息内容

        # st.chat_message 是 Streamlit 的"聊天气泡"组件
        # role 参数决定气泡在左边还是右边
        # "user" → 气泡在右边（蓝色），"assistant" → 气泡在左边（灰色）
        with st.chat_message(role):
            if role == "assistant":
                # AI 消息：以名字卡片形式展示
                # msg_idx 传进去，用于给收藏按钮生成唯一 key
                _display_names(content, msg_idx)
            else:
                # 用户消息：直接显示文字
                st.markdown(content)

    # ========== 底部输入框 ==========
    # 处理中或有待处理消息时，不显示输入框
    # 防止用户快速点多次，导致多个AI请求堆积
    if st.session_state.get('is_processing', False) or st.session_state.get('need_process', False):
        if st.session_state.get('is_processing', False):
            st.info("⏳ AI 正在思考中，请稍候...")
        user_input = None
    else:
        # st.chat_input 固定在页面底部
        # 用户按回车就触发
        user_input = st.chat_input("说出您的修改意见…（如：想要更文雅一点的名字）")

    if user_input and user_input.strip():
        # 把用户写的消息存入 session_state
        st.session_state.messages.append({
            "role": "user",
            "content": user_input.strip()
        })

        # 标记需要处理 → 告诉 app.py "快去调AI！"
        st.session_state.need_process = True

        # 刷新页面 → 先显示用户的消息，等 app.py 处理
        st.rerun()


def _display_names(names_data, msg_idx=0):
    """
    以卡片形式展示候选名字。

    参数：
        names_data: 名字数据，可以是字符串（AI返回的原始JSON）
                    或列表（已经解析好的Python对象）
        msg_idx: 这条消息是第几条对话，用于生成唯一key

    卡片布局：
    ┌──────┬────────────────────────┬──────┐
    │ 评分  │  张子轩阳              │  ☆  │
    │  🟢  │  📖 子：君子；轩：气宇  │ 收藏 │
    │  95   │  📚 出自《诗经》        │ 按钮 │
    │       │  🔥 五行：木            │      │
    └──────┴────────────────────────┴──────┘
    """
    # 如果 names_data 还是字符串，说明还没解析
    # 调用 parse_ai_response 把它转成列表
    if isinstance(names_data, str):
        names = parse_ai_response(names_data)
    elif isinstance(names_data, list):
        names = names_data
    else:
        st.warning("⚠️ 名字数据格式异常")
        return

    # 如果没有名字数据
    if not names:
        st.info("🤔 暂时没有名字数据")
        return

    # 逐个展示每个名字
    for i, name in enumerate(names):
        # 每张卡片分三列：左边评分 | 中间名字信息 | 右边收藏
        # [1,4,1] 表示中间列宽度是左右列的4倍
        col_score, col_info, col_action = st.columns([1, 4, 1])

        # ── 左边：评分 ──
        with col_score:
            score = name.get('score', 0) or 0
            if score >= 90: ring, txt = "#43A047", "#fff"
            elif score >= 80: ring, txt = "#D4AF37", "#fff"
            else: ring, txt = "#FB8C00", "#fff"
            st.markdown(
                f"<div style='display:flex;flex-direction:column;align-items:center;'>"
                f"<div style='width:46px;height:46px;border-radius:50%;background:{ring};"
                f"color:{txt};display:flex;align-items:center;justify-content:center;"
                f"font-weight:700;font-size:18px;box-shadow:0 3px 10px rgba(0,0,0,.12);'>{score}</div>"
                f"<span style='color:#8C8C8C;font-size:12px;margin-top:4px;'>评分</span></div>",
                unsafe_allow_html=True)

        # ── 中间：名字信息 ──
        with col_info:
            full_name = name.get('full_name') or name.get('name', '')
            st.markdown(
                f"<div class='gn-name' style='font-size:24px;'>{full_name}</div>",
                unsafe_allow_html=True)

            if name.get('_length_mismatch'):
                st.warning("⚠️ 字数未完全匹配，建议继续修改")

            meaning = name.get('meaning', '')
            if meaning:
                st.markdown(f"📖 *{meaning}*")

            cultural_ref = name.get('cultural_ref', '')
            if cultural_ref:
                st.markdown(f"📚 {cultural_ref}")

            # 五行属性 + 音韵分析（徽章形式）
            wuxing = name.get('wuxing', '')
            sound = name.get('sound_rhythm', '')
            tags = []
            if wuxing:
                tags.append(f"<span class='gn-tag'>🔥 五行：{wuxing}</span>")
            if sound:
                tags.append(f"<span class='gn-tag gn-tag-gray'>🎵 {sound}</span>")
            if tags:
                st.markdown("<div style='margin-top:6px;'>" + "".join(tags) + "</div>",
                            unsafe_allow_html=True)

        # ———— 用户评分与备注 ————
        name_id = name.get('id')
        if name_id:
            current_rating = name.get('user_rating', None) or 0
            current_note = name.get('user_note', '') or ''

            star_key = f"star_{name_id}_{msg_idx}_{i}"
            # 5 stars + label
            c1, c2, c3, c4, c5, cl = st.columns([1, 1, 1, 1, 1, 3])
            for s_idx, col in enumerate([c1, c2, c3, c4, c5]):
                with col:
                    is_filled = s_idx < current_rating
                    label = "★" if is_filled else "☆"
                    if st.button(label, key=f"{star_key}_{s_idx}",
                                 help=f"{s_idx+1} 星"):
                        save_user_rating(st.session_state.supabase, name_id, s_idx + 1)
                        name['user_rating'] = s_idx + 1
                        st.rerun()
            with cl:
                st.caption(f"{'⭐'*current_rating} {current_rating}分" if current_rating > 0 else "点击星星评分")

            # 备注
            new_note = st.text_input(
                "备注", value=current_note,
                key=f"note_{name_id}_{msg_idx}_{i}",
                placeholder="写下你的评价…",
                label_visibility="collapsed"
            )
            if new_note != current_note and name_id:
                save_user_note(st.session_state.supabase, name_id, new_note)
                name['user_note'] = new_note

        # ———— 右边：收藏按钮（功能预留） ————
        with col_action:
            is_fav = name.get('is_favorite', False)
            btn_label = "⭐" if is_fav else "☆"
            if st.button(
                btn_label,
                key=f"fav_{msg_idx}_{i}",
                help="收藏 / 取消收藏"):
                supabase = st.session_state.get('supabase')
                if supabase and name_id:
                    supabase.table("candidate_names") \
                        .update({"is_favorite": not is_fav}) \
                        .eq("id", name_id).execute()
                    name['is_favorite'] = not is_fav
                    st.rerun()

        # 名字之间的分隔线
        st.divider()
