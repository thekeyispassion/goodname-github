"""
个人中心 - 多页面版
子页面：余额与充值、修改密码（通过 session_state.profile_page 控制）
"""
import streamlit as st
from database.init import init_database as _init_db
from database.operations import (
    get_user_balance, add_balance, get_recharge_records,
    get_consumption_records, change_password, delete_user_account
)

st.set_page_config(page_title="个人中心", page_icon="👤", layout="wide")

# ── 注入新中式主题 ──
from ui.theme import apply_theme, render_topnav, card
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

uid = st.session_state.user_id
balance = get_user_balance(supabase, uid)
sub = st.session_state.get('profile_page', 'main')

# ── 顶部导航 ──
if render_topnav("profile", balance, st.session_state.user_email):
    st.session_state.remembered_email = st.session_state.user_email
    st.session_state.user_id = None; st.session_state.user_email = None
    st.query_params.clear(); st.switch_page("app.py")

# ═══════════════════════════════════════
# 子页面：充值
# ═══════════════════════════════════════
if sub == 'recharge':
    st.markdown(
        "<h3 style='font-family:\"Noto Serif SC\",serif;color:#2C2C2C;margin:6px 0 12px;'>"
        "💰 余额与充值</h3>", unsafe_allow_html=True)
    if st.button("← 返回个人中心", use_container_width=True):
        st.session_state.profile_page = "main"; st.rerun()

    # 余额大卡片
    st.markdown(f"""
    <div style="background:#FFF;border:1px solid #E5E0D8;border-radius:12px;
                padding:22px;box-shadow:0 4px 16px rgba(44,44,44,.05);
                border-top:3px solid #D4AF37;margin-bottom:12px;">
        <div style='color:#8C8C8C;font-size:14px;'>💰 当前余额</div>
        <div style='display:flex;align-items:baseline;gap:8px;margin:4px 0;'>
            <span style='font-size:52px;font-weight:700;color:#C43D3D;
                    font-family:\"Noto Serif SC\",serif;'>{balance}</span>
            <span style='color:#8C8C8C;'>次</span></div>
        <div style='color:#B0AAA0;font-size:13px;'>1 次 = 1 次取名生成</div>
    </div>""", unsafe_allow_html=True)

    plans = {"10次 (¥5.00)": (10,5.0), "30次 (¥12.00) 🏷️推荐": (30,12.0), "100次 (¥35.00) 🔥超值": (100,35.0)}
    selected = st.radio("充值档位", list(plans.keys()), index=1, label_visibility="collapsed")
    pay_method = st.selectbox("支付方式", ["支付宝", "微信支付", "银行卡"])
    if st.button("💳 立即充值", type="primary", use_container_width=True):
        amt, money = plans[selected]
        with st.spinner("模拟支付中..."):
            import time; time.sleep(1)
            add_balance(supabase, uid, amt, money, pay_method)
            st.success(f"✅ 充值成功！获得 {amt} 次"); st.balloons()
            st.session_state.profile_page = "main"; st.rerun()
    st.stop()

# ═══════════════════════════════════════
# 子页面：修改密码
# ═══════════════════════════════════════
if sub == 'password':
    _lp, _cp, _rp = st.columns([1, 1.4, 1])
    with _cp:
        st.markdown(
            "<div style='text-align:center;margin-bottom:8px;'>"
            "<h3 style='color:#C43D3D;font-family:\"Noto Serif SC\",serif;'>🔑 修改密码</h3></div>",
            unsafe_allow_html=True)
        if st.button("← 返回个人中心", use_container_width=True):
            st.session_state.profile_page = "main"; st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        old = st.text_input("当前密码", type="password", placeholder="请输入当前密码")
        new = st.text_input("新密码", type="password", help="至少8位，含大小写字母和数字",
                            placeholder="请设置新密码")
        confirm = st.text_input("确认新密码", type="password", placeholder="请再次输入新密码")
        if st.button("确认修改", type="primary", use_container_width=True):
            if not old or not new or not confirm: st.error("请填所有字段"); st.stop()
            if new != confirm: st.error("两次密码不一致"); st.stop()
            if len(new) < 8: st.error("密码至少8位"); st.stop()
            if new == old: st.error("新密码不能与旧密码相同"); st.stop()
            if change_password(supabase, old, new):
                st.success("✅ 修改成功！请重新登录")
                st.session_state.user_id = None; st.session_state.user_email = None
                st.session_state.profile_page = "main"; st.switch_page("app.py")
            else:
                st.error("❌ 当前密码错误")
        if st.button("取消", use_container_width=True):
            st.session_state.profile_page = "main"; st.rerun()
    st.stop()

# ═══════════════════════════════════════
# 子页面：注销账户
# ═══════════════════════════════════════
if sub == 'delete':
    _lp, _cp, _rp = st.columns([1, 1.3, 1])
    with _cp:
        st.markdown(
            "<div style='text-align:center;margin-bottom:8px;'>"
            "<h3 style='color:#C43D3D;font-family:\"Noto Serif SC\",serif;'>⚠️ 注销账户</h3></div>",
            unsafe_allow_html=True)
        if st.button("← 返回个人中心", use_container_width=True):
            st.session_state.profile_page = "main"; st.rerun()
        st.markdown(
            "<div style='background:#FFF5F5;border:1px solid #C43D3D;border-radius:12px;"
            "padding:14px 18px;margin:12px 0;color:#2C2C2C;font-size:14px;'>"
            "注销后所有取名记录、余额、充值记录将被<strong style='color:#C43D3D'>永久删除</strong>，无法恢复。"
            "</div>", unsafe_allow_html=True)
        pwd = st.text_input("请输入密码确认", type="password",
                            placeholder="输入密码以确认注销")
        with st.expander("📌 注销须知"):
            st.markdown("""
            - 你的所有取名记录将被删除
            - 余额和充值记录将被清空
            - 账户信息将从系统中移除
            - 此操作**不可撤销**
            """)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("确认注销", type="primary", use_container_width=True):
                if not pwd:
                    st.error("❌ 请输入密码确认"); st.stop()
                if delete_user_account(supabase, uid, pwd):
                    st.success("✅ 账户已注销")
                    st.session_state.user_id = None
                    st.session_state.user_email = None
                    st.session_state.profile_page = "main"
                    st.query_params.clear()
                    st.switch_page("app.py")
                else:
                    st.error("❌ 密码错误，无法注销")
        with col_d2:
            if st.button("取消", use_container_width=True):
                st.session_state.profile_page = "main"; st.rerun()
    st.stop()

# ═══════════════════════════════════════
# 个人中心主页
# ═══════════════════════════════════════
st.markdown(
    "<h3 style='font-family:\"Noto Serif SC\",serif;color:#2C2C2C;margin:6px 0 12px;'>"
    "👤 个人中心</h3>", unsafe_allow_html=True)

initial = (st.session_state.user_email or "?").strip()[0].upper()

c1, c2 = st.columns(2)
with c1:
    # 用户信息卡
    st.markdown(f"""
    <div style="background:#FFF;border:1px solid #E5E0D8;border-radius:12px;
                padding:20px;box-shadow:0 4px 16px rgba(44,44,44,.05);margin-bottom:16px;">
        <div style='text-align:center;'>
            <div style='display:inline-flex;align-items:center;justify-content:center;
                        width:64px;height:64px;border-radius:50%;background:#C43D3D;color:#fff;
                        font-size:28px;font-weight:700;box-shadow:0 4px 14px rgba(196,61,61,.25);
                        margin-bottom:10px;'>{initial}</div>
            <div style='font-weight:600;color:#2C2C2C;'>用户信息</div>
            <div style='color:#8C8C8C;font-size:14px;margin:6px 0;'>📧 {st.session_state.user_email}</div>
        </div>
    </div>""", unsafe_allow_html=True)

with c2:
    # 余额卡
    st.markdown(f"""
    <div style="background:#FFF;border:1px solid #E5E0D8;border-radius:12px;
                padding:20px;box-shadow:0 4px 16px rgba(44,44,44,.05);margin-bottom:16px;
                border-top:3px solid #D4AF37;">
        <div style='color:#8C8C8C;font-size:14px;'>💰 当前余额</div>
        <div style='display:flex;align-items:baseline;gap:8px;margin:4px 0;'>
            <span style='font-size:48px;font-weight:700;color:#C43D3D;
                    font-family:\"Noto Serif SC\",serif;'>{balance}</span>
            <span style='color:#8C8C8C;'>次</span></div>
        <div style='color:#B0AAA0;font-size:13px;margin-bottom:6px;'>1 次 = 1 次取名生成</div>
    </div>""", unsafe_allow_html=True)
    if st.button("⚡ 立即充值", type="primary", use_container_width=True):
        st.session_state.profile_page = "recharge"; st.rerun()
    # ── 测试账户余额控制 ──
    if st.session_state.user_email == "test@test.com":
        st.markdown("---")
        with st.expander("🔧 测试模式：控制余额"):
            new_bal = st.number_input("设置余额（次）", min_value=0, value=balance, step=10)
            if st.button("更新余额", use_container_width=True):
                current = supabase.table("user_balances").select("*").eq("user_id", uid).execute()
                if current.data:
                    supabase.table("user_balances").update({"balance": int(new_bal)}).eq("user_id", uid).execute()
                else:
                    supabase.table("user_balances").insert({"user_id": uid, "balance": int(new_bal)}).execute()
                st.success(f"余额已更新为 {int(new_bal)} 次")
                st.rerun()

    with st.expander("📄 充值记录"):
        recs = get_recharge_records(supabase, uid)[:20]
        if recs:
            for r in recs:
                st.markdown(f"`{(r.get('created_at') or '')[:16]}` +{r['amount']}次 (¥{r['money']})")
        else:
            st.caption("暂无充值记录")
    with st.expander("📄 消费记录"):
        cons = get_consumption_records(supabase, uid)[:20]
        if cons:
            for r in cons:
                amt = r['amount']; t = (r.get('created_at') or '')[:16]
                st.markdown(f"`{t}` {'🔴'+str(amt)+'次' if amt>0 else '🟢'+str(amt)+'次'} ({r.get('consumption_type','')})")
        else:
            st.caption("暂无消费记录")

# ── 操作卡网格：修改密码 / 退出登录 / 注销账户（一行三张）──
st.markdown(
    "<div style='font-weight:600;color:#2C2C2C;margin:8px 0 10px;'>账户操作</div>",
    unsafe_allow_html=True)
_a1, _a2, _a3 = st.columns(3)
with _a1:
    if st.button("🔑 修改密码", use_container_width=True, key="act_password",
                 help="修改账户登录密码"):
        st.session_state.profile_page = "password"; st.rerun()
with _a2:
    if st.button("🚪 退出登录", use_container_width=True, key="act_logout",
                 help="退出当前账户"):
        st.session_state.remembered_email = st.session_state.user_email
        st.session_state.user_id = None; st.session_state.user_email = None
        st.query_params.clear(); st.switch_page("app.py")
with _a3:
    if st.button("⚠️ 注销账户", use_container_width=True, key="act_delete",
                 help="永久删除账户及所有数据"):
        st.session_state.profile_page = "delete"; st.rerun()
