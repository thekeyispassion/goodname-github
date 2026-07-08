"""
全局主题（新中式极简风格）

⚠️ 只改样式，不碰功能逻辑，特别是侧边栏的隐藏展出状态机。
"""
import streamlit as st

# 色板（统一一处定义）
BG = "#F9F7F4"          # 暖白主背景
CARD = "#FFFFFF"        # 卡片纯白
PRIMARY = "#C43D3D"     # 朱砂红
PRIMARY_DARK = "#A52F2F"
GOLD = "#D4AF37"        # 淡金
INK = "#2C2C2C"         # 墨黑
GRAY = "#8C8C8C"        # 辅助灰
BORDER = "#E5E0D8"      # 表单边框

# 全局 CSS（每个页面调用一次）
_BASE_CSS = f"""
<style>
/* ============ 全局背景与字体 ============ */
html, body, [data-testid="stAppViewContainer"],
section[data-testid="stMain"],
div[data-testid="stAppViewContainer"] > section {{
    background-color: {BG} !important;
}}
#root, .stApp, [data-testid="stMain"] {{
    font-family: "PingFang SC", "Inter", "Microsoft YaHei", sans-serif !important;
    color: {INK} !important;
}}

/* ============ 主按钮（朱砂红） ============ */
button[kind="primary"],
div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 1px;
    box-shadow: 0 4px 14px rgba(196,61,61,.28) !important;
    transition: all .18s ease !important;
}}
button[kind="primary"]:hover {{
    box-shadow: 0 6px 20px rgba(196,61,61,.38) !important;
    transform: translateY(-1px);
}}

/* ============ 输入框/下拉框（圆角+浅灰边框） ============ */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div,
[data-testid="stDateInput"] input {{
    border-radius: 10px !important;
    border: 1px solid {BORDER} !important;
    background: {CARD} !important;
    transition: all .18s ease !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(196,61,61,.10) !important;
}}

/* ============ 侧边栏 ============ */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #FFFDF9 0%, {BG} 100%) !important;
    border-right: 1px solid {BORDER} !important;
}}
/* 侧边栏标题 */
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {{
    color: {INK} !important;
}}
/* 侧边栏折叠区 expander */
[data-testid="stExpanderToggleIcon"] {{
    color: {PRIMARY} !important;
}}

/* ============ 对话气泡 ============ */
[data-testid="stChatMessage"] {{
    border-radius: 14px !important;
    box-shadow: 0 2px 10px rgba(44,44,44,.05) !important;
    border: 1px solid {BORDER} !important;
}}

/* ============ 名字衬线体 ============ */
.gn-name {{
    font-family: "Noto Serif SC", "Songti SC", "STSong", serif !important;
    color: {INK};
    font-weight: 600;
    letter-spacing: 2px;
}}

/* ============ 标签徽章 ============ */
.gn-tag {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 12px;
    background: #FBF3E0;
    color: {PRIMARY};
    border: 1px solid {GOLD};
    margin-right: 6px;
}}
.gn-tag-gray {{
    background: #F2EEE8; color: {GRAY}; border-color: {BORDER};
}}

/* ============ 滚动条 ============ */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-thumb {{ background: #d8d3cb; border-radius: 8px; }}
::-webkit-scrollbar-track {{ background: transparent; }}

/* ============ page_link 样式 ============ */
[data-testid="stPageLink-NavLink"] a {{
    border-radius: 10px !important;
    color: {GRAY} !important;
    transition: all .15s ease !important;
}}
[data-testid="stPageLink-NavLink"] a:hover {{
    color: {PRIMARY} !important;
    background: #FBF3E0 !important;
}}

/* ============ 登录/注册居中卡片 ============ */
.gn-auth-wrap {{
    display:flex; justify-content:center; padding-top:24px;
}}
.gn-auth-card {{
    background:{CARD};
    border:1px solid {BORDER};
    border-radius:18px;
    box-shadow:0 12px 40px rgba(44,44,44,.08);
    padding:38px 40px 30px;
    max-width:420px; width:100%;
}}
.gn-auth-logo {{
    text-align:center; margin-bottom:6px;
}}
.gn-auth-logo .gn-seal {{
    display:inline-flex; align-items:center; justify-content:center;
    width:52px; height:52px; border-radius:12px;
    background:{PRIMARY}; color:#fff; font-size:26px; font-weight:700;
    box-shadow:0 8px 20px rgba(196,61,61,.30);
}}
</style>
"""


def apply_theme():
    """注入全局主题 CSS（每个页面调用一次）"""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def render_topnav(current: str, balance: int, email: str) -> bool:
    """
    统一顶部导航栏（登录/注册页除外）——单条 64px 栏，对齐 v2.0 规范。

    布局：[品牌 logo+名称]  [取名主页][历史记录][个人中心]  [余额徽章]  [退出登录]
    当前所在页 tab 高亮朱砂红；个人中心当前页时文字前带首字母头像。

    返回：True 表示用户点了「退出登录」
    ⚠️ 仅布局，不碰任何业务逻辑。Streamlit 自带顶栏保留不动。
    """
    initial = (email or "?").strip()[0].upper()

    # —— 单条导航栏：一行 columns 拼出全部内容（品牌/三个tab/余额/退出）——
    # c1 品牌 | c2 主页 | c3 历史 | c4 个人中心 | c5 余额 | c6 退出
    c1, c2, c3, c4, c5, c6 = st.columns([2.4, 1, 1, 1.2, 1.4, 1])

    with c1:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;"
            f"font-family:\"Noto Serif SC\",serif;font-weight:700;font-size:19px;color:{INK};'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:34px;height:34px;border-radius:8px;background:{PRIMARY};color:#fff;"
            f"font-size:18px;box-shadow:0 3px 10px rgba(196,61,61,.30);'>印</span>"
            f"<span>智能取名系统</span></div>", unsafe_allow_html=True)

    def _tab(col, active, page, label, label_active, with_avatar=False):
        with col:
            if active:
                avatar = ""
                if with_avatar:
                    avatar = (f"<span style='display:inline-flex;align-items:center;"
                              f"justify-content:center;width:24px;height:24px;border-radius:50%;"
                              f"background:{PRIMARY};color:#fff;font-size:12px;font-weight:700;"
                              f"margin-right:6px;'>{initial}</span>")
                st.markdown(
                    f"<div style='display:flex;align-items:center;justify-content:center;"
                    f"font-weight:700;color:{PRIMARY};padding:8px 0;"
                    f"border-bottom:2px solid {PRIMARY};'>{avatar}{label_active}</div>",
                    unsafe_allow_html=True)
            else:
                st.page_link(page, label=label, use_container_width=True)

    _tab(c2, current == "home", "pages/1_取名主页.py", "取名主页", "取名主页")
    _tab(c3, current == "history", "pages/2_历史记录.py", "历史记录", "历史记录")
    _tab(c4, current == "profile", "pages/3_个人中心.py", "个人中心", "个人中心", with_avatar=True)

    with c5:
        st.markdown(
            f"<div style='display:flex;align-items:center;justify-content:center;'>"
            f"<span style='background:#FBF3E0;color:{PRIMARY};border:1px solid {GOLD};"
            f"border-radius:999px;padding:6px 14px;font-weight:600;font-size:14px;'>"
            f"💰 余额 {balance} 次</span></div>", unsafe_allow_html=True)

    with c6:
        if st.button("退出登录", use_container_width=True, key=f"logout_{current}",
                     help="退出当前账户"):
            return True

    # 导航栏底部 1px 浅灰分割线
    st.markdown(
        f"<div style='border-bottom:1px solid {BORDER};margin:-6px 0 14px;'></div>",
        unsafe_allow_html=True)
    return False


def card(html: str, variant: str = "") -> str:
    """生成卡片 HTML（用 st.markdown 渲染）"""
    border_top = ""
    if variant == "gold":
        border_top = f"border-top:3px solid {GOLD};"
    elif variant == "red":
        border_top = f"border-top:3px solid {PRIMARY};"
    return (
        f'<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;'
        f'padding:20px 22px;box-shadow:0 4px 16px rgba(44,44,44,.05);margin-bottom:16px;'
        f'{border_top}">{html}</div>'
    )