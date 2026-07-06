"""
数据库操作模块

作用：封装所有和数据库"说话"的操作。
每个函数只做一件事，方便 app.py 调用。

【数据库里有什么表？】
1. naming_sessions      — 每次取名请求是一条记录（存用户填的表单数据）
2. candidate_names      — AI生成的每个名字是一条记录
3. conversation_messages — 用户和AI的每句对话是一条记录

【SQL 基础知识】
- INSERT INTO 表名 (字段...) VALUES (值...)  → 插入一条新数据
- SELECT 字段 FROM 表名 WHERE 条件          → 查询数据
- UPDATE 表名 SET 字段=新值 WHERE 条件       → 修改数据
- DELETE FROM 表名 WHERE 条件               → 删除数据
- 问号 ? 是占位符，防止 SQL 注入攻击（重要！）
"""
import sqlite3
import uuid
from datetime import datetime


def create_session(conn, user_input: dict) -> str:
    """
    创建一次新的取名会话。

    参数：
        conn: 数据库连接（由 app.py 从 st.session_state 取出）
        user_input: 用户在表单填的所有信息（字典格式）

    返回值：
        session_id: 一个全局唯一的ID（UUID），用来关联其他表

    举例：
        用户填了"张"姓 + "男孩" + "4个字"
        → 数据库加一条记录，返回 "a1b2c3d4-..." 这样的ID

    UUID 长这样：'550e8400-e29b-41d4-a716-446655440000'
    特点：全世界几乎不会重复，比用 1,2,3 自增id 安全
    """
    session_id = str(uuid.uuid4())  # 生成唯一ID

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO naming_sessions
        (session_id, surname, gender, birth_date, birth_time,
         name_length, preferences, avoid_words, family_info, cultural_prefs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        user_input.get('surname', ''),     # 姓氏
        user_input.get('gender', ''),      # 性别
        user_input.get('birth_date'),      # 出生日期
        user_input.get('birth_time'),      # 出生时辰
        user_input.get('name_length'),     # 选的总字数
        user_input.get('preferences'),     # 寓意偏好
        user_input.get('avoid_words'),     # 避讳字
        user_input.get('family_info'),     # 家庭信息
        user_input.get('cultural_prefs'),  # 传统文化偏好
    ))

    conn.commit()  # 提交更改，数据才真正写入文件
    print(f"✅ 创建会话：{session_id}")
    return session_id


def save_names(conn, session_id: str, names: list, round_number: int = 1):
    """
    保存 AI 生成的一批候选名字到数据库。

    参数：
        conn: 数据库连接
        session_id: 这次生成属于哪个会话
        names: AI返回的名字列表，例如：
            [
                {"name": "子轩阳", "full_name": "张子轩阳",
                 "meaning": "子：君子", "score": 95},
                {"name": "明浩然", "full_name": "张明浩然",
                 "meaning": "明：光明", "score": 91}
            ]
        round_number: 第几轮（首次=1，修改一次+1）

    逻辑：
        遍历 names 列表，每个名字插入一条 candidate_names 记录。
        score 字段需要做"钳位处理"——防止 AI 返回 None 或超出范围的值。
    """
    cursor = conn.cursor()

    for name_data in names:
        cursor.execute("""
            INSERT INTO candidate_names
            (session_id, round_number, name_text, full_name,
             meaning, cultural_ref, wuxing, sound_rhythm, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            round_number,
            name_data.get('name', ''),               # 名字本身
            name_data.get('full_name', ''),           # 全名
            name_data.get('meaning', ''),             # 字义解析
            name_data.get('cultural_ref', ''),        # 文化出处
            name_data.get('wuxing', ''),              # 五行属性
            name_data.get('sound_rhythm', ''),        # 音韵分析
            # ⚠️ score 钳位处理：
            #   name_data.get('score') 可能为 None
            #   None or 80 = 80（默认给80分）
            #   min(100, ...) = 最高100
            #   max(1, ...) = 最低1
            max(1, min(100, name_data.get('score') or 80)),
        ))

    conn.commit()
    print(f"✅ 保存了 {len(names)} 个名字（第{round_number}轮）")


def save_message(conn, session_id: str, role: str, content: str, round_number: int = 1):
    """
    保存一条对话消息。

    参数：
        conn: 数据库连接
        session_id: 属于哪个会话
        role: 'user' 或 'assistant'
        content: 消息内容（用户说的话 或 AI 的回复）
        round_number: 第几轮

    这个表记录了完整的对话历史，用途：
    - 用户刷新页面后可以恢复聊天记录
    - 多轮优化时给AI提供上下文（之前说过什么）
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation_messages (session_id, role, content, round_number)
        VALUES (?, ?, ?, ?)
    """, (session_id, role, content, round_number))
    conn.commit()


def get_history(conn, session_id: str) -> list:
    """
    查询某个会话的全部对话历史。

    参数：
        conn: 数据库连接
        session_id: 会话ID

    返回值：
        列表，每个元素是 Row 对象，可以用下标或字段名访问：
        msg['role']      → 'user' 或 'assistant'
        msg['content']   → 消息内容
        msg['created_at'] → 发送时间

    按时间从早到晚排序（ORDER BY created_at ASC）。
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, round_number, created_at
        FROM conversation_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    """, (session_id,))
    return cursor.fetchall()


def get_session_info(conn, session_id: str):
    """
    查询某个会话的用户填表信息。

    参数：
        session_id: 会话ID

    返回值：
        Row 对象，包含用户最初填的所有表单信息。
        可以这样用：
            info['surname']  → 姓氏
            info['name_length'] → 选的字数
        如果 session_id 不存在，返回 None。
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM naming_sessions WHERE session_id = ?
    """, (session_id,))
    return cursor.fetchone()


def get_candidate_names(conn, session_id: str, round_number: int = None) -> list:
    """
    查询某个会话生成的名字。

    参数：
        conn: 数据库连接
        session_id: 会话ID
        round_number: 指定查第几轮（不填则返回所有轮次）

    返回值：
        名字列表，按评分从高到低排序。
        每个元素是 Row 对象：
            name['full_name']   → 全名
            name['name_text']   → 名字本身
            name['meaning']     → 字义
            name['score']       → 评分
    """
    cursor = conn.cursor()

    if round_number is not None:
        # 查指定轮次
        cursor.execute("""
            SELECT * FROM candidate_names
            WHERE session_id = ? AND round_number = ?
            ORDER BY score DESC
        """, (session_id, round_number))
    else:
        # 查所有轮次（最新轮次排前面，同轮次高分排前面）
        cursor.execute("""
            SELECT * FROM candidate_names
            WHERE session_id = ?
            ORDER BY round_number DESC, score DESC
        """, (session_id,))

    return cursor.fetchall()


def update_session_status(conn, session_id: str, status: str, is_satisfied: bool = False):
    """
    更新会话状态（当用户结束对话时调用）。

    参数：
        conn: 数据库连接
        session_id: 会话ID
        status: 'active'（进行中）或 'completed'（已结束）
        is_satisfied: 用户最终是否满意
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE naming_sessions
        SET status = ?, is_satisfied = ?, updated_at = ?
        WHERE session_id = ?
    """, (status, is_satisfied, datetime.now(), session_id))
    conn.commit()
    print(f"✅ 更新会话 {session_id} 状态为：{status}")


# ========== 单独运行测试 ==========
# 当你直接执行 python database/operations.py 时运行
# 不会影响 app.py 的正常运行
if __name__ == "__main__":
    import sys
    import os
    # 把项目根目录加入 Python 的导入路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from database.init import init_database

    conn = init_database()

    # 测试创建会话
    test_input = {
        'surname': '张',
        'gender': '男孩',
        'birth_date': '2026-08-15',
        'birth_time': '未时',
        'name_length': '3个字',
        'preferences': '希望孩子聪明智慧',
        'avoid_words': None,
    }
    session_id = create_session(conn, test_input)
    print(f"   会话ID：{session_id}")

    # 测试保存名字
    test_names = [
        {"name": "致远", "full_name": "张致远", "meaning": "专注投入，志向远大", "score": 95},
        {"name": "明哲", "full_name": "张明哲", "meaning": "明辨是非，智慧通达", "score": 90},
    ]
    save_names(conn, session_id, test_names, round_number=1)

    # 测试保存消息
    save_message(conn, session_id, "user", "帮我取个名字", round_number=1)
    save_message(conn, session_id, "assistant", "好的，为您推荐以下名字", round_number=1)

    # 测试查询
    history = get_history(conn, session_id)
    print(f"\n📋 对话历史 ({len(history)} 条)：")
    for msg in history:
        print(f"   [{msg['role']}] {msg['content'][:30]}...")

    names = get_candidate_names(conn, session_id)
    print(f"\n📋 候选名字 ({len(names)} 个)：")
    for n in names:
        print(f"   {n['full_name']} - {n['meaning']} (评分：{n['score']})")

    conn.close()
