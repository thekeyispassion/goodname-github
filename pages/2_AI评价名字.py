"""
AI评价名字页
"""
import streamlit as st
from database.init import init_database as _init_db
from database.operations import (
    get_user_balance, deduct_balance,
    save_evaluation, get_evaluation_history
)
from llm.client import call_deepseek
from llm.prompt_builder import build_evaluate_prompt
st.set_page_config(page_title="AI评价名字", page_icon="🤖", layout="wide")

# ── 注入新中式主题 ──
from ui.theme import apply_theme, render_topnav
apply_theme()

# 移除左侧栏
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

if st.session_state.get('user_id'):
    if "uid" not in st.query_params:
        st.query_params["uid"] = st.session_state.user_id
    if "email" not in st.query_params:
        st.query_params["email"] = st.session_state.user_email

if not st.session_state.get('user_id'):
    st.warning("请先登录"); st.page_link("app.py", label="去登录", icon="🔑"); st.stop()

uid = st.session_state.user_id
balance = get_user_balance(supabase, uid)

# ── 顶部导航 ──
if render_topnav("evaluate", balance, st.session_state.user_email):
    st.session_state.remembered_email = st.session_state.user_email
    st.session_state.user_id = None; st.session_state.user_email = None
    st.query_params.clear(); st.switch_page("app.py")

# ── 页面标题 ──
st.markdown(
    "<h3 style='font-family:\"Noto Serif SC\",serif;color:#2C2C2C;margin:6px 0 4px;'>"
    "🤖 AI 评价名字</h3>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#8C8C8C;font-size:14px;margin:0 0 16px;'>"
    "输入一个名字，让 AI 为您深度解析</p>",
    unsafe_allow_html=True)

# ── 输入区 ──
col_input, col_btn = st.columns([5, 1])
with col_input:
    name_to_eval = st.text_input(
        "名字", placeholder="请输入要评价的名字，如：子轩",
        label_visibility="collapsed", key="eval_name_input"
    )
with col_btn:
    eval_clicked = st.button("评价", type="primary", use_container_width=True)

# ── 评价逻辑 ──
if eval_clicked:
    if not name_to_eval or not name_to_eval.strip():
        st.error("❌ 请输入要评价的名字")
    elif get_user_balance(supabase, uid) < 1:
        st.error("❌ 余额不足，请先充值")
        if st.button("⚡ 去充值", type="primary"):
            st.session_state.profile_page = "recharge"
            st.switch_page("pages/4_个人中心.py")
    else:
        st.session_state.eval_processing = True
        st.session_state.eval_name = name_to_eval.strip()
        st.rerun()

# ── 处理评价请求 ──
if st.session_state.get('eval_processing', False):
    name_text = st.session_state.get('eval_name', '')
    with st.spinner(f"🤔 AI 正在分析「{name_text}」..."):
        deduct_balance(supabase, uid, None, "evaluate")
        msgs = build_evaluate_prompt(name_text)
        resp = call_deepseek(msgs)
        if resp:
            import json, re
            # 评价接口返回单个 JSON 对象，非数组
            result = {}
            try:
                # 直接解析
                result = json.loads(resp)
            except json.JSONDecodeError:
                # 尝试提取 JSON 代码块
                m = re.search(r'```(?:json)?\s*\n?(\{.*?\})\n?```', resp, re.DOTALL)
                if m:
                    try:
                        result = json.loads(m.group(1))
                    except json.JSONDecodeError:
                        pass
                # 尝试模糊匹配花括号
                if not result:
                    m = re.search(r'\{[^{}]*\}', resp)
                    if m:
                        try:
                            result = json.loads(m.group(0))
                        except json.JSONDecodeError:
                            result = {"overall_score": 0, "comment": resp}
            if not isinstance(result, dict):
                result = {"overall_score": 0, "comment": resp}
            save_evaluation(supabase, uid, name_text, result)
            st.session_state.eval_result = result
            st.session_state.eval_done_name = name_text
        else:
            st.error("❌ AI 暂不可用，请稍后重试")
            st.session_state.eval_result = None
    st.session_state.eval_processing = False
    st.rerun()

# ── 展示评价结果 ──
if st.session_state.get('eval_result'):
    result = st.session_state.eval_result
    name_text = st.session_state.get('eval_done_name', '')
    overall = result.get('overall_score', 0) or 0

    # 总分圆环颜色
    if overall >= 85: ring = "#43A047"
    elif overall >= 70: ring = "#D4AF37"
    else: ring = "#FB8C00"

    st.markdown("---")
    st.markdown(f"""
    <div style="background:#FFF;border:1px solid #E5E0D8;border-radius:14px;
                padding:24px 28px;box-shadow:0 4px 20px rgba(44,44,44,.06);">
        <div style='display:flex;align-items:center;gap:20px;flex-wrap:wrap;'>
            <!-- 总分圆环 -->
            <div style='display:flex;flex-direction:column;align-items:center;min-width:80px;'>
                <div style='width:72px;height:72px;border-radius:50%;background:{ring};
                            color:#fff;display:flex;align-items:center;justify-content:center;
                            font-weight:700;font-size:30px;font-family:"Noto Serif SC",serif;
                            box-shadow:0 4px 16px rgba(0,0,0,.15);'>{overall}</div>
                <span style='color:#8C8C8C;font-size:12px;margin-top:4px;'>综合评分</span>
            </div>
            <!-- 名字 + 维度 -->
            <div style='flex:1;min-width:250px;'>
                <div class='gn-name' style='font-size:28px;margin-bottom:12px;'>{name_text}</div>
                <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;'>
                    <div style='font-size:13px;color:#2C2C2C;'>📖 字义：<b>{result.get('meaning_score',0) or 0}</b> 分</div>
                    <div style='font-size:13px;color:#2C2C2C;'>🎵 音韵：<b>{result.get('sound_score',0) or 0}</b> 分</div>
                    <div style='font-size:13px;color:#2C2C2C;'>📚 文化：<b>{result.get('culture_score',0) or 0}</b> 分</div>
                    <div style='font-size:13px;color:#2C2C2C;'>🔥 五行：<b>{result.get('wuxing_score',0) or 0}</b> 分</div>
                </div>
            </div>
        </div>
        <!-- 评语 -->
        <div style='margin-top:18px;padding:14px 18px;background:#F9F7F4;border-radius:10px;
                    color:#2C2C2C;font-size:15px;line-height:1.8;'>
            📝 {result.get('comment', '暂无评语')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── 初始引导 ──
if not st.session_state.get('eval_result') and not st.session_state.get('eval_processing'):
    st.markdown("""
    <div style='text-align:center;padding:60px 20px 0;color:#B0AAA0;'>
        <div style='font-size:56px;margin-bottom:12px;'>🤖</div>
        <p style='font-size:16px;'>输入名字后点击「评价」，AI 将为您多维度分析</p>
        <p style='font-size:13px;'>每次评价消耗 1 次余额</p>
    </div>
    """, unsafe_allow_html=True)

# ── 评价历史 ──
st.markdown("---")
st.markdown(
    "<h4 style='font-family:\"Noto Serif SC\",serif;color:#2C2C2C;margin:8px 0 10px;'>"
    "📋 评价历史</h4>", unsafe_allow_html=True)

history = get_evaluation_history(supabase, uid)
if history:
    for h in history:
        score = h.get('overall_score', 0) or 0
        sc = "#43A047" if score >= 85 else ("#D4AF37" if score >= 70 else "#FB8C00")
        st.markdown(f"""
        <div style="background:#FFF;border:1px solid #E5E0D8;border-radius:10px;
                    padding:12px 16px;box-shadow:0 2px 8px rgba(44,44,44,.04);
                    margin-bottom:8px;display:flex;align-items:center;gap:14px;">
            <span class='gn-name' style='font-size:18px;'>{h.get('name_text','')}</span>
            <span style='display:inline-flex;align-items:center;justify-content:center;
                        width:38px;height:38px;border-radius:50%;background:{sc};color:#fff;
                        font-weight:700;font-size:16px;'>{score}</span>
            <span style='color:#8C8C8C;font-size:13px;flex:1;'>
                {h.get('comment','')[:60]}{'…' if len(h.get('comment','') or '')>60 else ''}</span>
            <span style='color:#B0AAA0;font-size:12px;'>{(h.get('created_at') or '')[:16]}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.caption("暂无评价记录，输入名字开始评价吧")
