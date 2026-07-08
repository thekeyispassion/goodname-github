"""
历史记录页面

作用：展示当前登录用户的所有取名记录。
用户可以点击某条记录查看详情（对话和候选名字）。
"""
import streamlit as st
from database.operations import get_user_sessions, get_candidate_names, get_history


def render_history_page(supabase):
    """
    渲染历史记录页面。

    流程：
        1. 从 Supabase 查询当前用户的所有 naming_sessions
        2. 以列表形式展示（日期、姓氏、性别、状态）
        3. 用户点某条 → 展开查看详细名字和对话
    """
    st.markdown("# 📋 取名历史记录")
    st.markdown("---")

    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("请先登录")
        return

    # 查询用户的取名记录
    with st.spinner("加载中..."):
        sessions = get_user_sessions(supabase, user_id)

    if not sessions:
        st.info("你还没有取名记录，去首页试试吧！")
        return

    st.caption(f"共 {len(sessions)} 条记录")

    # 逐条展示
    for s in sessions:
        created = s.get('created_at', '')[:10] if s.get('created_at') else '未知日期'
        surname = s.get('surname', '')
        gender = s.get('gender', '')
        name_length = s.get('name_length', '')
        satisfied = s.get('is_satisfied', False)
        session_id = s.get('session_id', '')

        status_icon = "✅" if satisfied else "⏳"
        gender_icon = "👦" if gender == "男孩" else "👧"

        with st.expander(f"{status_icon} {created}  {gender_icon} {surname}姓 {name_length or ''}"):
            # 显示该次会话生成的所有名字
            names = get_candidate_names(supabase, session_id)
            if names:
                st.markdown("**生成的名字：**")
                for n in names:
                    score = n.get('score', '')
                    full_name = n.get('full_name', n.get('name_text', ''))
                    meaning = n.get('meaning', '')
                    line = f"- {full_name}"
                    if score:
                        line += f"（评分 {score}）"
                    if meaning:
                        line += f"：{meaning}"
                    st.markdown(line)

            # 显示对话摘要
            messages = get_history(supabase, session_id)
            if messages:
                st.markdown("**对话摘要：**")
                feedbacks = [m['content'][:50] for m in messages if m['role'] == 'user' and len(m['content']) < 100]
                for fb in feedbacks[:3]:  # 最多显示3条用户意见
                    st.markdown(f"  💬 {fb}..." if len(fb) >= 50 else f"  💬 {fb}")
