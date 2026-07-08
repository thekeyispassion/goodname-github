"""
数据库操作模块（难度2 → Supabase 版本）

和难度1的区别：
- 不再传 conn（SQLite 连接），改传 supabase（云客户端）
- 不再写 SQL 语句，改调用 supabase.table().xxx().execute()
- 所有函数加 user_id 参数，数据归属于登录用户

Supabase API 速查：
    插入：supabase.table("表名").insert({"字段": "值"}).execute()
    查询：supabase.table("表名").select("*").eq("字段", 值).execute()
    排序：.order("字段", desc=True)
    返回：result.data 是列表，每个元素是字典
"""
import uuid
from datetime import datetime


def create_session(supabase, user_input: dict, user_id: str = None) -> str:
    """
    创建新的取名会话，返回 session_id。
    难度2新增：传入 user_id 关联当前登录用户。
    """
    session_id = str(uuid.uuid4())

    data = {
        'session_id': session_id,
        'user_id': user_id,
        'surname': user_input.get('surname', ''),
        'gender': user_input.get('gender', ''),
        'birth_date': user_input.get('birth_date'),
        'birth_time': user_input.get('birth_time'),
        'name_length': user_input.get('name_length'),
        'preferences': user_input.get('preferences'),
        'avoid_words': user_input.get('avoid_words'),
        'family_info': user_input.get('family_info'),
        'cultural_prefs': user_input.get('cultural_prefs'),
    }

    result = supabase.table("naming_sessions").insert(data).execute()
    print(f"✅ 创建会话：{session_id}")
    return session_id


def save_names(supabase, session_id: str, names: list, round_number: int = 1):
    """保存 AI 生成的一批候选名字到 Supabase。"""
    records = []
    for name_data in names:
        records.append({
            'session_id': session_id,
            'round_number': round_number,
            'name_text': name_data.get('name', ''),
            'full_name': name_data.get('full_name', ''),
            'meaning': name_data.get('meaning', ''),
            'cultural_ref': name_data.get('cultural_ref', ''),
            'wuxing': name_data.get('wuxing', ''),
            'sound_rhythm': name_data.get('sound_rhythm', ''),
            'score': max(1, min(100, name_data.get('score') or 80)),
        })

    result = supabase.table("candidate_names").insert(records).execute()
    print(f"✅ 保存了 {len(records)} 个名字（第{round_number}轮）")


def save_message(supabase, session_id: str, role: str, content: str, round_number: int = 1):
    """保存一条对话消息到 Supabase。"""
    data = {
        'session_id': session_id,
        'role': role,
        'content': str(content) if isinstance(content, (dict, list)) else content,
        'round_number': round_number,
    }
    supabase.table("conversation_messages").insert(data).execute()


def get_history(supabase, session_id: str) -> list:
    """读取某个会话的全部对话历史（按时间排序）。"""
    result = supabase.table("conversation_messages") \
        .select("role, content, round_number, created_at") \
        .eq("session_id", session_id) \
        .order("created_at") \
        .execute()
    return result.data  # 列表，每项是 {"role":..., "content":..., ...}


def get_session_info(supabase, session_id: str):
    """读取某个会话的用户填表信息。"""
    result = supabase.table("naming_sessions") \
        .select("*") \
        .eq("session_id", session_id) \
        .execute()
    return result.data[0] if result.data else None


def get_candidate_names(supabase, session_id: str, round_number: int = None) -> list:
    """读取某个会话生成的名字，按评分降序。"""
    query = supabase.table("candidate_names") \
        .select("*") \
        .eq("session_id", session_id)

    if round_number is not None:
        query = query.eq("round_number", round_number)

    result = query.order("score", desc=True).execute()
    return result.data


def update_session_status(supabase, session_id: str, status: str, is_satisfied: bool = False):
    """更新会话状态。"""
    supabase.table("naming_sessions") \
        .update({"status": status, "is_satisfied": is_satisfied, "updated_at": datetime.now().isoformat()}) \
        .eq("session_id", session_id) \
        .execute()
    print(f"✅ 更新会话 {session_id} 状态为：{status}")


def get_user_sessions(supabase, user_id: str) -> list:
    """获取某个用户的所有取名会话（难度2新增：历史记录用）。"""
    result = supabase.table("naming_sessions") \
        .select("session_id, surname, gender, name_length, created_at, is_satisfied") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()
    return result.data


# ========== 单独测试 ==========
if __name__ == "__main__":
    from database.init import init_database

    supabase = init_database()
    if not supabase:
        print("❌ 请先配置 Supabase 连接")
        exit()

    # 测试创建会话（需要先登录，拿到 user_id）
    test_input = {
        'surname': '张',
        'gender': '男孩',
        'name_length': '3个字',
        'preferences': '希望孩子聪明智慧',
    }
    session_id = create_session(supabase, test_input, user_id=None)
    print(f"   会话ID：{session_id}")
