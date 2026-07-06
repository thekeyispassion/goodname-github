"""
取名大师 - 主入口 ★★★ 这是整个程序的起点 ★★★

你运行 streamlit run app.py 的时候，电脑就会执行这个文件。

【整个程序的运行流程】（建议先看这个，再看代码）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

用户打开网页
    │
    ▼
左侧显示表单（sidebar.py） ← 用户填姓氏、性别、字数等
    │
    ▼  用户点击「开始取名」
程序收到表单数据，存入 st.session_state（内存里）
    │
    ▼
情况A：首次生成
    │
    ├─ 1. 建数据库会话（database/operations.py → create_session）
    ├─ 2. 拼提示词（llm/prompt_builder.py → build_initial_prompt）
    ├─ 3. 调 DeepSeek API（llm/client.py → call_deepseek）
    ├─ 4. 解析返回结果（utils/parser.py → parse_ai_response）
    ├─ 5. 校验字数（本文件的 _validate_name_lengths）
    └─ 6. 展示给用户（ui/chat_area.py → render_chat_area）
    │
    ▼
用户不满意，在底部输入框写修改意见
    │
    ▼
情况B：多轮优化（流程和上面差不多，调的是 build_refine_prompt）
    │
    ▼
用户满意 → 结束

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【重要概念解释】
- st.session_state：Streamlit 的"内存仓库"。页面每刷新一次，
  普通变量就丢了，但存在 st.session_state 里的东西不会丢。
  你可以把它想象成一个柜子，每格放一个数据。

- conn：数据库连接。程序通过 conn 和 SQLite 文件对话。
  存数据：conn.execute("INSERT...")
  取数据：conn.execute("SELECT...")

- 本文件不直接干活，它是"总指挥"——决定什么时候调用哪个模块。
"""
import streamlit as st
from database.init import init_database
from database.operations import (
    create_session,      # 创建一次取名会话（存到数据库）
    save_message,        # 保存一条对话消息（用户/AI说的每句话）
    save_names,          # 保存AI生成的一批名字
)
from llm.client import call_deepseek
from llm.prompt_builder import build_initial_prompt, build_refine_prompt, _get_name_char_count
from utils.parser import parse_ai_response
from ui.sidebar import render_sidebar       # 画左侧表单的函数
from ui.chat_area import render_chat_area   # 画右侧对话的函数


# ════════════════════════════════════════════════════════════
# 第0步：辅助函数（放在最前面，因为后面要用）
# ════════════════════════════════════════════════════════════

def _get_expected_chars(user_input):
    """
    计算：用户说"4个字"，名字本身应该有几个字？

    参数 user_input 是字典，里面存了用户在表单填的所有信息。
    user_input = {
        'surname': '张',        ← 姓氏
        'name_length': '4个字',  ← 用户选的总字数
        ...
    }

    比如 user_input['name_length']='4个字'，代表"姓+名=4个字"。
    减去姓氏（默认1个字），名字本身 = 4-1 = 3个字。

    如果姓氏是"欧阳"（2个字），名字本身 = 4-2 = 2个字。
    """
    surname = user_input.get('surname', '')
    # _get_name_char_count 在 prompt_builder.py 里，
    # 它负责把"4个字"转成数字3（名取3个字）
    return _get_name_char_count(user_input.get('name_length', ''), surname)


def _validate_name_lengths(names, user_input):
    """
    AI 返回名字后，逐一检查每个名字的字数对不对。

    参数：
        names: AI返回的名字列表，比如 [
            {'name': '子轩阳', 'full_name': '张子轩阳', 'score': 95},
            {'name': '致远',   'full_name': '张致远',   'score': 90}
        ]
        user_input: 用户在表单填的信息

    如果某个名字字数不对，给它打个标记 _length_mismatch = True，
    展示的时候会显示 ⚠️ 警告。
    字数对的标记为 False（不警告）。
    """
    # 先算期望的字数（比如期望名字有3个字）
    expected = _get_expected_chars(user_input)
    if expected is None:
        return names  # 用户没选字数，就不校验了

    validated = []
    for name in names:
        # name.get('name', '') 从每个名字字典里取出 'name' 字段
        # 比如 {'name': '子轩阳'} → name_text = '子轩阳'
        name_text = name.get('name', '')
        if name_text and len(name_text) != expected:
            print(f"⚠️ 名字「{name.get('full_name', name_text)}」字数{len(name_text)}!=期望{expected}")
            name['_length_mismatch'] = True  # 打标记：字数不对
        else:
            name['_length_mismatch'] = False  # 字数正确
        validated.append(name)

    return validated


# ════════════════════════════════════════════════════════════
# 第1步：页面配置（必须是第 1 行 Streamlit 代码）
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="取名大师",        # 浏览器标签页上显示的文字
    page_icon="📛",              # 标签页上的小图标
    layout="wide",               # "wide"=宽屏，"centered"=窄屏
    initial_sidebar_state="expanded",  # 侧边栏默认展开
)


# ════════════════════════════════════════════════════════════
# 第2步：初始化 st.session_state（程序启动时只执行一次）
#
# 为什么要用 if 'xxx' not in st.session_state？
# Streamlit 的特性：每次用户点按钮、输入文字，整个脚本会
# 从头到尾重新执行一遍。如果不用 if 判断，每次重跑都会重新
# 初始化，之前存的数据就丢了。
#
# 所以写法是：如果这个变量还不存在，就创建它。
# 如果已经存在，说明不是第一次运行，保留旧值。
# ════════════════════════════════════════════════════════════

# ---- 数据库连接 ----
# 连接上 goodname.db 文件，之后所有数据库操作都用这个 conn
# init_database() 在 database/init.py 里，负责创建表
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = init_database()

# ---- 对话消息列表 ----
# 存用户和AI的所有对话，格式是列表，每个元素是一个字典：
#   [{"role": "user", "content": "帮我取名字"},
#    {"role": "assistant", "content": [...]}]
# role 是 "user"（用户说的）或 "assistant"（AI说的）
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ---- 轮次计数 ----
# 第1次生成 = 1，用户提修改意见后重新生成 = 2，以此类推
if 'round_number' not in st.session_state:
    st.session_state.round_number = 0

# ---- 会话ID ----
# 每次用户填表点"开始取名"就生成一个唯一ID（UUID）
# 用来关联数据库里的记录
if 'session_id' not in st.session_state:
    st.session_state.session_id = None

# ---- 是否已提交信息 ----
# False = 还没填表，显示表单页面
# True  = 已经填了，显示对话页面
if 'info_submitted' not in st.session_state:
    st.session_state.info_submitted = False

# ---- 是否需要处理 ----
# 用户发了新消息后设为 True，告诉程序"快去调AI！"
if 'need_process' not in st.session_state:
    st.session_state.need_process = False

# ---- 正在处理锁 ----
# True  = AI正在工作中，此时隐藏输入框，防止用户又发消息
# False = 空闲状态，可以输入
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

# ---- 用户填的表单数据 ----
# 存姓氏、性别、字数等，格式是字典
if 'user_input' not in st.session_state:
    st.session_state.user_input = {}


# ════════════════════════════════════════════════════════════
# 第3步：页面布局（控制网页上显示什么）
#
# Streamlit 的页面结构：
# ┌──────────────┬────────────────────────────────┐
# │  侧边栏       │      主区域                    │
# │  (st.sidebar)│                              │
# │              │                              │
# │  表单/信息    │  欢迎页 / 对话页面             │
# │              │                              │
# └──────────────┴────────────────────────────────┘
# ════════════════════════════════════════════════════════════

# ===== 左侧：侧边栏 =====
# st.sidebar 代表浏览器左侧的窄条区域
with st.sidebar:
    st.markdown("# 📛 取名大师")

    if st.session_state.info_submitted:
        # ---- 已提交：显示精简摘要 ----
        # 用户已经填过表了，侧边栏只显示一行摘要 + 可折叠修改区
        info = st.session_state.user_input
        st.info(
            f"👤 {info.get('surname', '')}姓 {info.get('gender', '')} "
            f"{' | ' + info.get('name_length', '') if info.get('name_length') else ''}"
        )
        # st.expander 是"可折叠区域"，点击展开才能看到完整表单
        with st.expander("📝 查看/修改信息"):
            render_sidebar()  # 这个函数在 ui/sidebar.py 里
    else:
        # ---- 未提交：显示完整表单 ----
        render_sidebar()


# ===== 右侧：主区域 =====
if not st.session_state.info_submitted:
    # 还没填表 → 显示欢迎页面
    # st.columns(3) 把页面分成3列，[1,2,1] 表示中间列宽度是两侧的2倍
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # unsafe_allow_html=True 表示允许在markdown里写HTML标签
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
    # 已填表 → 显示对话页面
    render_chat_area()


# ════════════════════════════════════════════════════════════
# 第4步：业务逻辑（核心！决定了程序怎么运转）
#
# 这里有两个"情况"，触发条件不同：
#
# 情况A：用户刚提交表单 → 第一次调AI生成名字
# 条件：info_submitted=True（已填表）且 session_id=None（还没生成过）
#
# 情况B：用户提了修改意见 → 让AI优化
# 条件：need_process=True（有新的用户消息要处理）
#
# 注意：情况A和情况B不会同时触发，因为第一次生成后
# session_id 就不再是 None 了。
# ════════════════════════════════════════════════════════════

# ——————— 情况A：首次提交表单，生成名字 ———————
# 这个 if 条件翻译成人话：
# "用户已经填好了表，但还没开始第一次生成"
if st.session_state.info_submitted and st.session_state.session_id is None:
    st.session_state.is_processing = True  # 上锁，不让用户乱点
    conn = st.session_state.db_conn        # 取出数据库连接

    # st.spinner 显示一个转圈动画，让用户知道"正在处理中"
    with st.spinner("🤔 正在根据信息取名中..."):

        # 【第1步】创建数据库会话
        # create_session 在 database/operations.py 里
        # 它把用户填的表单数据写到 goodname.db 的 naming_sessions 表
        # 返回一个唯一的 session_id（字符串）
        session_id = create_session(conn, st.session_state.user_input)
        st.session_state.session_id = session_id
        st.session_state.round_number = 1

        # 【第2步】构建提示词
        # build_initial_prompt 在 llm/prompt_builder.py 里
        # 它把用户的表单信息 + 系统指令 + 格式要求，拼成
        # DeepSeek API 能识别的消息列表
        # 返回格式：[{"role": "system", ...}, {"role": "user", ...}]
        messages = build_initial_prompt(st.session_state.user_input)

        # 【第3步】保存用户消息到数据库
        # messages[-1] 是最后一条消息（用户填的信息）
        # save_message 会把这条消息存到 conversation_messages 表
        user_content = messages[-1]["content"]
        save_message(conn, session_id, "user", user_content, round_number=1)

        # 【第4步】调用 DeepSeek API
        # call_deepseek 在 llm/client.py 里
        # 它把提示词发给 DeepSeek 的服务器，等AI回复
        # 如果成功，返回 AI 写的文本（JSON字符串）
        # 如果失败，返回 None
        response = call_deepseek(messages)

        if response:
            # 【第5步】解析 AI 返回的结果
            # AI 返回的是字符串，比如：
            # '[{"name": "子轩阳", "full_name": "张子轩阳", ...}]'
            # parse_ai_response 把它转成 Python 列表（好操作）
            names = parse_ai_response(response)

            # 【第5.5步】校验字数
            if names:
                names = _validate_name_lengths(names, st.session_state.user_input)

            # 【第6步】保存到数据库
            save_message(conn, session_id, "assistant", response, round_number=1)
            if names:
                save_names(conn, session_id, names, round_number=1)

            # 【第7步】存入 session_state，用于页面展示
            # 如果解析成功，存解析后的列表（好渲染）
            # 如果解析失败（比如AI返回了奇怪的东西），存原始文本
            display_content = names if names else response
            st.session_state.messages.append({
                "role": "assistant",
                "content": display_content
            })
        else:
            # API 调用失败 → 显示错误信息
            st.error("❌ AI 暂时无法响应，请稍后重试")
            error_msg = (
                "抱歉，我现在无法连接到 AI 服务。请检查：\n\n"
                "1. **API Key** 是否正确（配置在 `.env` 文件中）\n"
                "2. **网络**是否正常\n"
                "3. 是否超过 API **调用限额**"
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })

        # 解锁，用户现在可以输入了
        st.session_state.is_processing = False

        # 刷新页面，显示 AI 的回复
        # st.rerun() 让 Streamlit 从头再跑一次脚本
        # 这次 st.session_state 里有新内容了，页面会更新
        st.rerun()


# ——————— 情况B：用户输入了修改意见，进行优化 ———————
# 这个 if 条件翻译成人话：
# "用户发了新消息，需要让AI修改名字"
if st.session_state.get('need_process', False):
    st.session_state.need_process = False   # 关掉待处理标记
    st.session_state.is_processing = True    # 上锁
    conn = st.session_state.db_conn
    session_id = st.session_state.session_id

    # 轮次 +1（第2轮、第3轮……）
    st.session_state.round_number += 1
    round_num = st.session_state.round_number

    # 获取用户最新的输入
    # st.session_state.messages[-1] 是消息列表的最后一条
    # 也就是用户刚刚在输入框里写的那句话
    if st.session_state.messages:
        user_feedback = st.session_state.messages[-1]["content"]
    else:
        user_feedback = ""

    with st.spinner(f"🔄 第 {round_num} 轮优化中..."):

        # 【第1步】构建优化提示词
        # 和情况A不同，这次调的是 build_refine_prompt
        # 它会把"原始需求 + 之前推荐的名字 + 用户新意见"一起发给AI
        # 这样AI就知道之前给了什么名字、用户哪里不满意
        #
        # st.session_state.messages[:-1] 是"除了最后一条之外的所有消息"
        # 最后一条是用户刚写的意见，单独作为 user_feedback 传进去
        history = st.session_state.messages[:-1]
        messages = build_refine_prompt(
            st.session_state.user_input,
            history,
            user_feedback
        )

        # 【第2步】保存用户意见到数据库
        save_message(conn, session_id, "user", user_feedback, round_number=round_num)

        # 【第3步】调 API
        response = call_deepseek(messages)

        if response:
            # 【第4步】解析
            names = parse_ai_response(response)

            # 【第4.5步】校验字数
            if names:
                names = _validate_name_lengths(names, st.session_state.user_input)

            # 【第5步】保存到数据库
            save_message(conn, session_id, "assistant", response, round_number=round_num)
            if names:
                save_names(conn, session_id, names, round_number=round_num)

            # 【第6步】展示
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

        # 解锁
        st.session_state.is_processing = False

        # 刷新页面
        st.rerun()
