"""
个人中心 - 多页面版
子页面：余额与充值、修改密码（通过 session_state.profile_page 控制）
"""
import streamlit as st
from database.init import init_database as _init_db
from database.operations import (
    get_user_balance, add_balance, get_recharge_records,
    get_consumption_records, change_password
)

st.set_page_config(page_title="个人中心", page_icon="👤", layout="wide")

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
cols = st.columns([2, 1, 1, 2, 1, 1])
with cols[0]: st.markdown("### 📛 智能取名系统")
with cols[1]: st.page_link("pages/1_取名主页.py", label="取名主页")
with cols[2]: st.page_link("pages/2_历史记录.py", label="历史记录")
with cols[3]: st.markdown(f"<h4 style='text-align:right'>💰 余额：{balance}次</h4>", unsafe_allow_html=True)
with cols[4]: st.markdown("##### ✅ 个人中心")
with cols[5]:
    if st.button("🚪 退出"):
        st.session_state.remembered_email = st.session_state.user_email
        st.session_state.user_id = None; st.session_state.user_email = None
        st.query_params.clear(); st.switch_page("app.py")
st.markdown("---")

# ═══════════════════════════════════════
# 子页面：充值
# ═══════════════════════════════════════
if sub == 'recharge':
    st.markdown("## 💰 余额与充值")
    if st.button("← 返回"): st.session_state.profile_page = "main"; st.rerun()
    st.markdown(f"<h2 style='color:#C43D3D;'>{balance} 次</h2>", unsafe_allow_html=True)

    plans = {"10次 (¥5.00)": (10,5.0), "30次 (¥12.00) 🏷️": (30,12.0), "100次 (¥35.00) 🔥": (100,35.0)}
    selected = st.radio("充值档位", list(plans.keys()), index=1)
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
    st.markdown("## 🔑 修改密码")
    if st.button("← 返回"): st.session_state.profile_page = "main"; st.rerun()
    old = st.text_input("当前密码", type="password")
    new = st.text_input("新密码", type="password", help="至少8位，含大小写字母和数字")
    confirm = st.text_input("确认新密码", type="password")
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
    st.stop()

# ═══════════════════════════════════════
# 个人中心主页
# ═══════════════════════════════════════
st.markdown("## 👤 个人中心")

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### 用户信息")
    st.markdown(f"📧 **邮箱**：{st.session_state.user_email}")
    if st.button("🔑 修改密码", use_container_width=True):
        st.session_state.profile_page = "password"; st.rerun()
    if st.button("🚪 退出登录", use_container_width=True):
        st.session_state.remembered_email = st.session_state.user_email
        st.session_state.user_id = None; st.session_state.user_email = None
        st.query_params.clear(); st.switch_page("app.py")

with c2:
    st.markdown("#### 💰 当前余额")
    st.markdown(f"<h1 style='color:#C43D3D;font-size:48px;'>{balance}</h1>", unsafe_allow_html=True)
    if st.button("⚡ 立即充值", type="primary", use_container_width=True):
        st.session_state.profile_page = "recharge"; st.rerun()
    with st.expander("📄 充值记录"):
        for r in get_recharge_records(supabase, uid)[:20]:
            st.markdown(f"`{(r.get('created_at') or '')[:16]}` +{r['amount']}次 (¥{r['money']})")
    with st.expander("📄 消费记录"):
        for r in get_consumption_records(supabase, uid)[:20]:
            amt = r['amount']; t = (r.get('created_at') or '')[:16]
            st.markdown(f"`{t}` {'🔴'+str(amt)+'次' if amt>0 else '🟢'+str(amt)+'次'} ({r.get('consumption_type','')})")
