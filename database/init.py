"""
数据库初始化模块（难度2 → Supabase 版本）

作用：连接 Supabase 云数据库，返回客户端对象。
Supabase 的表需要在网页后台的 SQL Editor 中手动创建，
建表语句见同目录下的 supabase_schema.sql。
"""
import os
from supabase import create_client


def _load_env():
    """
    从 .env 文件读取配置（和 llm/client.py 一样的逻辑）。
    因为 Streamlit 不会自动加载 .env 文件。
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def init_database(st_session=None):
    """
    连接 Supabase，返回客户端对象。
    参数 st_session: 可选，Streamlit 的 st.session_state，
                    若有已保存的认证 token 则自动恢复登录态。

    用法：
        supabase = init_database(st.session_state)
        # 然后用 supabase 操作数据库

    如果 SUPABASE_URL 或 SUPABASE_KEY 没配置，返回 None。
    """
    # 先从 .env 文件读
    env = _load_env()
    url = env.get('SUPABASE_URL', '')
    key = env.get('SUPABASE_KEY', '')

    # 如果 .env 没有，再尝试环境变量
    if not url:
        url = os.environ.get("SUPABASE_URL", "")
    if not key:
        key = os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        print("⚠️ SUPABASE_URL 或 SUPABASE_KEY 未配置，请在 .env 中设置")
        return None

    try:
        supabase = create_client(url, key)

        # 恢复认证会话（页面刷新后 RLS 需要 auth.uid()）
        if st_session is not None:
            try:
                saved = st_session.get('_supabase_session')
                if saved and saved.get('access_token'):
                    supabase.auth.set_session(
                        saved['access_token'],
                        saved.get('refresh_token', '')
                    )
            except Exception:
                pass  # 恢复失败不阻塞初始化

        # 测试连接是否有效（做个简单查询）
        supabase.table("naming_sessions").select("id").limit(1).execute()
        print("✅ Supabase 连接成功")
        return supabase
    except Exception as e:
        print(f"❌ Supabase 连接失败：{e}")
        return None
