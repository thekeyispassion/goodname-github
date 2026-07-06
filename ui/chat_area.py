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
        user_input = st.chat_input("输入修改意见（如：想要更文雅一点的名字）")

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

        # ———— 左边：评分 ————
        with col_score:
            score = name.get('score', 0) or 0
            # 评分颜色：≥90 绿色，≥80 黄色，<80 橙色
            if score >= 90:
                score_icon = "🟢"
            elif score >= 80:
                score_icon = "🟡"
            else:
                score_icon = "🟠"
            st.markdown(f"### {score_icon}")
            st.caption(f"评分 {score}")

        # ———— 中间：名字信息 ————
        with col_info:
            # 全名（姓氏+名字）
            full_name = name.get('full_name') or name.get('name', '')
            st.markdown(f"### **{full_name}**")

            # 字数不匹配时显示警告
            if name.get('_length_mismatch'):
                st.warning("⚠️ 字数未完全匹配，建议继续修改")

            # 字义解析
            meaning = name.get('meaning', '')
            if meaning:
                st.markdown(f"📖 *{meaning}*")

            # 文化出处
            cultural_ref = name.get('cultural_ref', '')
            if cultural_ref:
                st.markdown(f"📚 {cultural_ref}")

            # 五行属性 + 音韵分析（放同一行）
            wuxing = name.get('wuxing', '')
            sound = name.get('sound_rhythm', '')
            tags = []
            if wuxing:
                tags.append(f"🔥 五行：{wuxing}")
            if sound:
                tags.append(f"🎵 {sound}")
            if tags:
                st.markdown(" | ".join(tags))

        # ———— 右边：收藏按钮（功能预留） ————
        with col_action:
            is_fav = name.get('is_favorite', False)
            btn_label = "⭐" if is_fav else "☆"
            st.button(
                btn_label,
                # key 的组成：fav + 消息序号 + 名字序号
                # 比如第2条AI回复的第3个名字 → "fav_1_2"
                # 这样确保每个按钮的 key 都是唯一的
                key=f"fav_{msg_idx}_{i}",
                help="收藏该名字（功能待完善）",
                disabled=True  # 暂时禁用，后续再开发
            )

        # 名字之间的分隔线
        st.divider()
