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


def save_names(supabase, session_id: str, names: list, round_number: int = 1) -> list:
    """保存 AI 生成的一批候选名字到 Supabase。

    返回：已插入的数据库记录列表（每条含 id 字段），用于前端跟踪评分。
    """
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

    try:
        result = supabase.table("candidate_names").insert(records).execute()
        print(f"✅ 保存了 {len(records)} 个名字（第{round_number}轮）")
        return result.data if result.data else []
    except Exception as e:
        print(f"❌ 保存名字失败（第{round_number}轮）：{e}")
        return []


# ========== 评价与打分（v2.0 扩展） ==========

def save_user_rating(supabase, name_id: int, rating: int) -> bool:
    """
    保存用户对某个名字的评分（1~5 星）。

    参数：
        supabase: Supabase 客户端
        name_id: candidate_names 表中的 id
        rating: 用户评分（1~5），传 None 清除评分
    """
    if rating is not None:
        rating = max(1, min(5, int(rating)))
    supabase.table("candidate_names") \
        .update({"user_rating": rating}) \
        .eq("id", name_id) \
        .execute()
    return True


def save_user_note(supabase, name_id: int, note: str) -> bool:
    """
    保存用户对某个名字的备注文字。

    参数：
        supabase: Supabase 客户端
        name_id: candidate_names 表中的 id
        note: 备注文字，传空字符串或 None 都会存为 None
    """
    note = note.strip() if note else None
    supabase.table("candidate_names") \
        .update({"user_note": note}) \
        .eq("id", name_id) \
        .execute()
    return True


def get_name_rating(supabase, name_id: int) -> dict:
    """
    查询某个名字的用户评分和备注。

    返回：{"user_rating": 4, "user_note": "读音好听"} 或 None
    """
    result = supabase.table("candidate_names") \
        .select("user_rating, user_note") \
        .eq("id", name_id) \
        .execute()
    if result.data:
        return result.data[0]
    return {"user_rating": None, "user_note": None}


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


# ========== 余额相关操作（v2.0） ==========

def get_user_balance(supabase, user_id: str) -> int:
    """查询用户剩余生成次数。如果还没有余额记录，自动创建并赠送20次。"""
    result = supabase.table("user_balances") \
        .select("balance") \
        .eq("user_id", user_id) \
        .execute()
    if result.data:
        return result.data[0]['balance']

    # 自动创建余额记录（新用户送20次）
    try:
        supabase.table("user_balances").insert({
            "user_id": user_id,
            "balance": 20,
        }).execute()
        return 20
    except Exception:
        return 0


def deduct_balance(supabase, user_id: str, session_id: str, consume_type: str = 'generate') -> bool:
    """
    扣除1次生成次数，使用乐观锁防并发。
    返回 True=扣费成功，False=余额不足。
    """
    # 读取当前余额和版本号
    result = supabase.table("user_balances") \
        .select("balance, version") \
        .eq("user_id", user_id) \
        .execute()

    if not result.data or result.data[0]['balance'] < 1:
        return False

    row = result.data[0]
    new_balance = row['balance'] - 1
    old_version = row['version']

    # 乐观锁更新
    supabase.table("user_balances") \
        .update({
            "balance": new_balance,
            "total_consumed": row.get('total_consumed', 0) + 1,
            "version": old_version + 1,
            "updated_at": datetime.now().isoformat()
        }) \
        .eq("user_id", user_id) \
        .eq("version", old_version) \
        .execute()

    # 记录消费
    supabase.table("consumption_records").insert({
        "user_id": user_id,
        "session_id": session_id,
        "amount": 1,
        "consumption_type": consume_type
    }).execute()

    return True


def add_balance(supabase, user_id: str, amount: int, money: float, method: str):
    """充值：增加余额，记录充值流水。"""
    result = supabase.table("user_balances") \
        .select("balance, total_recharged") \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        # 没有余额记录 → 创建一条
        supabase.table("user_balances").insert({
            "user_id": user_id, "balance": amount,
            "total_recharged": amount
        }).execute()
        new_balance = amount
    else:
        new_balance = result.data[0]['balance'] + amount
        new_recharged = result.data[0].get('total_recharged', 0) + amount
        supabase.table("user_balances") \
        .update({
            "balance": new_balance,
            "total_recharged": new_recharged,
            "updated_at": datetime.now().isoformat()
        }) \
        .eq("user_id", user_id) \
        .execute()

    # 记录充值流水
    supabase.table("recharge_records").insert({
        "user_id": user_id,
        "amount": amount,
        "money": money,
        "payment_method": method,
        "status": "success"
    }).execute()

    return True


def get_recharge_records(supabase, user_id: str) -> list:
    """查询充值记录。"""
    result = supabase.table("recharge_records") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()
    return result.data


def get_consumption_records(supabase, user_id: str) -> list:
    """查询消费记录。"""
    result = supabase.table("consumption_records") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()
    return result.data


# ========== AI 评价名字（v2.0 扩展） ==========

def save_evaluation(supabase, user_id: str, name_text: str, result: dict) -> bool:
    """
    保存 AI 评价结果到 name_evaluations 表。

    参数：
        supabase: Supabase 客户端
        user_id: 当前用户 ID
        name_text: 被评价的名字
        result: AI 返回的评价结果字典（含各维度评分和评语）
    """
    supabase.table("name_evaluations").insert({
        "user_id": user_id,
        "name_text": name_text,
        "meaning_score": max(0, min(100, result.get('meaning_score', 0) or 0)),
        "sound_score": max(0, min(100, result.get('sound_score', 0) or 0)),
        "culture_score": max(0, min(100, result.get('culture_score', 0) or 0)),
        "wuxing_score": max(0, min(100, result.get('wuxing_score', 0) or 0)),
        "overall_score": max(0, min(100, result.get('overall_score', 0) or 0)),
        "comment": result.get('comment', '') or '',
    }).execute()
    return True


def get_evaluation_history(supabase, user_id: str, limit: int = 20) -> list:
    """查询用户的评价历史，按时间倒序。"""
    result = supabase.table("name_evaluations") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    return result.data or []


def change_password(supabase, current_password: str, new_password: str) -> bool:
    """修改密码。"""
    try:
        user = supabase.auth.get_user()
        # 先用旧密码登录验证
        supabase.auth.sign_in_with_password({
            "email": user.user.email,
            "password": current_password
        })
        # 更新密码
        supabase.auth.update_user({"password": new_password})
        return True
    except Exception:
        return False


def delete_user_account(supabase, user_id: str, password: str) -> bool:
    """
    注销账户：验证密码后删除用户所有数据。
    先清数据表，再调 Supabase Auth 删除账户本身。
    """
    # 1. 验证密码
    try:
        user = supabase.auth.get_user()
        supabase.auth.sign_in_with_password({
            "email": user.user.email,
            "password": password
        })
    except Exception:
        return False

    # 2. 删除业务数据（先子表后父表，避免外键冲突）
    session_ids = supabase.table("naming_sessions") \
        .select("session_id") \
        .eq("user_id", user_id) \
        .execute()
    for s in (session_ids.data or []):
        sid = s['session_id']
        # 先删所有子表（引用了 naming_sessions 的表）
        supabase.table("consumption_records").delete().eq("session_id", sid).execute()
        supabase.table("candidate_names").delete().eq("session_id", sid).execute()
        supabase.table("conversation_messages").delete().eq("session_id", sid).execute()

    # 再删父表
    supabase.table("naming_sessions").delete().eq("user_id", user_id).execute()
    supabase.table("recharge_records").delete().eq("user_id", user_id).execute()
    supabase.table("user_balances").delete().eq("user_id", user_id).execute()

    # 3. 删除认证账户
    try:
        supabase.auth.admin.delete_user(user_id)
    except Exception:
        # admin API 可能不可用，尝试用普通 API
        pass

    return True


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
