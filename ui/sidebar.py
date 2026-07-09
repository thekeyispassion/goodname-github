"""
左侧信息采集面板

作用：画网页左侧的表单，让用户填写取名信息。
相当于你去医院挂号时填的那张表——填完交给"医生"（AI）处理。

重要知识点：
- 这个函数不包含 with st.sidebar，由 app.py 负责放在侧边栏
- 这样既能用在"首次填写"（完整表单），也能用在"修改信息"（折叠区域）
- 所有数据通过 st.session_state 传递给 app.py
"""
import streamlit as st
from ui.theme import auto_error


def render_sidebar():
    """
    画左侧表单。

    返回：
        True  - 用户点了「开始取名」按钮
        False - 还没点

    按钮点击后做的事：
        1. 校验输入（姓氏必须填、避讳字不能等于姓氏、字数必须选）
        2. 把表单数据存到 st.session_state.user_input
        3. 如果是修改模式，清除旧会话，重新生成
        4. 标记 info_submitted = True，通知 app.py "可以开始生成了"
    """
    st.markdown(
        "<div style='margin-bottom:6px;'>"
        "<h3 style='margin:0;color:#2C2C2C;font-family:\"Noto Serif SC\",serif;'>📝 宝宝信息</h3>"
        "<p style='color:#8C8C8C;font-size:13px;margin:4px 0 0;'>填写以下信息，AI 将为您智能取名</p>"
        "</div><hr style='border-color:#E5E0D8;margin:12px 0;'>",
        unsafe_allow_html=True)

    # ── 基础信息区 ──
    st.markdown(
        "<div style='font-weight:600;color:#C43D3D;font-size:15px;margin-bottom:8px;'>"
        "▎基础信息</div>", unsafe_allow_html=True)

    # ---- 姓氏输入框 ----
    # st.text_input 生成一个文本框
    # value 是默认值（从 session_state 取上次填的，方便修改模式）
    # key 是 Streamlit 的"身份证"，每个组件不能重名
    surname = st.text_input(
        "姓氏 *",  # * 表示必填
        placeholder="请输入姓氏，如：张",
        value=st.session_state.get('surname', ''),
        key="input_surname"
    )

    # ---- 性别 ----
    # st.radio 是单选按钮
    # index=0 默认选中"男孩"，index=1 选中"女孩"
    gender = st.radio(
        "性别 *",
        ["男孩", "女孩"],
        index=0 if st.session_state.get('gender') != '女孩' else 1,
        key="input_gender"
    )

    # ---- 出生日期和时辰（左右并排） ----
    # st.columns(2) 把这一行分成左右两列
    col1, col2 = st.columns(2)
    with col1:
        # st.date_input 是日期选择器
        birth_date = st.date_input(
            "出生日期",
            value=None,
            key="input_birth_date"
        )
    with col2:
        # st.selectbox 是下拉选择框
        # 12个时辰对应古代一天12个时段
        birth_time = st.selectbox(
            "出生时辰",
            ["", "子时(23-1)", "丑时(1-3)", "寅时(3-5)", "卯时(5-7)",
             "辰时(7-9)", "巳时(9-11)", "午时(11-13)", "未时(13-15)",
             "申时(15-17)", "酉时(17-19)", "戌时(19-21)", "亥时(21-23)"],
            key="input_birth_time"
        )

    # ---- 名字总字数 ----
    # 注意：这里的"4个字"是指"姓氏+名字"的总字数
    # 选了"4个字" → AI知道要取3个字的名（比如"张子轩阳"）
    name_length = st.selectbox(
        "名字总字数（含姓）",
        ["", "2个字", "3个字", "4个字"],
        key="input_name_length"
    )

    # ── 补充信息（选填） ──
    with st.expander("📌 是否有其他需求？"):
        preferences = st.text_area(
            "寓意偏好",
            placeholder="如：希望孩子聪明智慧、健康平安、事业有成",
            key="input_preferences"
        )

        avoid_words = st.text_input(
            "避讳字",
            placeholder="如：刚、强、龙（多个用逗号隔开）",
            key="input_avoid_words"
        )

        cultural_prefs = st.text_area(
            "传统文化偏好",
            placeholder="如：希望名字出自《诗经》、五行缺金",
            key="input_cultural_prefs"
        )

    st.markdown("<hr style='border-color:#E5E0D8;margin:14px 0;'>", unsafe_allow_html=True)

    # ── 确定按钮 ──
    clicked = st.button(
        "🎯 确定 / 开始取名",
        type="primary",
        use_container_width=True
    )

    # ———————————————————— 按钮点击后的处理 ————————————————————
    if clicked:
        # 【校验1】姓氏不能为空
        if not surname.strip():
            auto_error("请填写姓氏")
            return False

        # 【校验2】避讳字里不能有姓氏
        # 解释：避讳字是"不能用的字"，姓氏是"家族的字"
        # 如果避讳字里包含姓氏，相当于"不能用自己家的字"，不合逻辑
        # avoid_words.split(',') 把"刚,强,龙"变成 ["刚","强","龙"]
        if avoid_words and surname.strip() in [w.strip() for w in avoid_words.split(',')]:
            auto_error(f"避讳字不能包含姓氏「{surname.strip()}」")
            return False

        # 【校验3】字数必须选
        if not name_length:
            auto_error("请选择名字总字数")
            return False

        # 【通过校验】收集所有表单数据，存到 session_state
        # 这样 app.py 就能读到用户填了什么
        st.session_state.user_input = {
            'surname': surname.strip(),
            'gender': gender,
            'birth_date': str(birth_date) if birth_date else None,
            'birth_time': birth_time if birth_time else None,
            'name_length': name_length if name_length else None,
            'preferences': preferences.strip() if preferences else None,
            'avoid_words': avoid_words.strip() if avoid_words else None,
            'cultural_prefs': cultural_prefs.strip() if cultural_prefs else None,
            'family_info': None,  # 难度1暂不收集，留空
        }

        # ★ 判断：这是"修改模式"还是"首次填写"？
        # 如果是修改模式（info_submitted 已经是 True），
        # 需要清空旧会话，重新开始
        if st.session_state.get('info_submitted', False):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.session_state.round_number = 0
            st.session_state.need_process = False

        # 标记信息已提交 → app.py 中的 情况A 会被触发
        st.session_state.info_submitted = True

        # 弹出绿色成功提示
        st.success(f"✅ 已收到 {surname.strip()} 姓的信息！正在为您取名...")
        return True

    return False
