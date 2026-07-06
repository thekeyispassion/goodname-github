"""
数据库初始化模块

作用：创建 SQLite 数据库文件和三张核心表。
只要运行一次，表就会自动创建（如果不存在的话）。
"""
import sqlite3
import os

# 数据库文件路径（默认在项目根目录）
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "goodname.db")


def init_database(db_path=None):
    """
    创建数据库和所有表（如果表不存在）。

    用法：
        conn = init_database()          # 默认文件 goodname.db
        conn = init_database("test.db") # 指定文件名

    返回：
        数据库连接对象（conn），后续所有操作都用这个对象。
    """
    if db_path is None:
        db_path = DB_PATH

    # check_same_thread=False：允许 Streamlit 在不同线程中复用同一个连接
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 让查询结果能用 row['字段名'] 访问

    cursor = conn.cursor()

    # 使用 executescript 一次性执行多条 SQL 语句
    cursor.executescript("""
        -- ========== 表1：取名会话表 ==========
        -- 用户每次填写表单并点击"确定"，就创建一条会话记录。
        CREATE TABLE IF NOT EXISTS naming_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            surname TEXT NOT NULL,
            gender TEXT NOT NULL CHECK(gender IN ('男孩', '女孩')),
            birth_date TEXT,
            birth_time TEXT,
            name_length TEXT,
            preferences TEXT,
            avoid_words TEXT,
            family_info TEXT,
            cultural_prefs TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed')),
            is_satisfied BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- ========== 表2：候选名字表 ==========
        -- AI每生成一个名字，这里就多一条记录。
        CREATE TABLE IF NOT EXISTS candidate_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES naming_sessions(session_id),
            round_number INTEGER NOT NULL,
            name_text TEXT NOT NULL,
            full_name TEXT NOT NULL,
            meaning TEXT,
            cultural_ref TEXT,
            wuxing TEXT,
            sound_rhythm TEXT,
            score INTEGER CHECK(score >= 1 AND score <= 100),
            is_favorite BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- ========== 表3：对话消息表 ==========
        -- 用户和AI的每一句对话都存下来，刷新页面后可以恢复。
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES naming_sessions(session_id),
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            round_number INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    print(f"✅ 数据库初始化成功：{db_path}")
    return conn


# ========== 单独测试 ==========
if __name__ == "__main__":
    conn = init_database()

    # 查看有哪些表
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("📋 已创建的表：")
    for t in tables:
        # 查询每个表的行数
        cursor.execute(f"SELECT COUNT(*) FROM {t['name']}")
        count = cursor.fetchone()[0]
        print(f"   - {t['name']} ({count} 条记录)")

    conn.close()
