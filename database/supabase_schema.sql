-- =============================================================
-- Supabase 数据库建表语句
-- 使用方式：打开 Supabase 后台 → SQL Editor → 粘贴运行
-- =============================================================

-- 1. 取名会话表（原 SQLite 同名表 + 新增 user_id）
CREATE TABLE naming_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    user_id UUID REFERENCES auth.users(id),        -- 关联 Supabase 用户
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
    is_satisfied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 候选名字表（和原 SQLite 完全一致）
CREATE TABLE candidate_names (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES naming_sessions(session_id),
    round_number INTEGER NOT NULL,
    name_text TEXT NOT NULL,
    full_name TEXT NOT NULL,
    meaning TEXT,
    cultural_ref TEXT,
    wuxing TEXT,
    sound_rhythm TEXT,
    score INTEGER,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 对话消息表（和原 SQLite 完全一致）
CREATE TABLE conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES naming_sessions(session_id),
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    round_number INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 用户信息表（Supabase 自动创建 auth.users，这里存额外信息）
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    username TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 当新用户注册时自动创建 profile
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, username)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'username');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 触发器：用户注册后自动调用
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- =============================================================
-- 行级安全策略（RLS）- 用户只能看自己的数据
-- =============================================================

-- naming_sessions：用户只能看自己的会话
ALTER TABLE naming_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "用户只能操作自己的命名会话"
    ON naming_sessions
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- candidate_names：通过 naming_sessions 关联到用户
ALTER TABLE candidate_names ENABLE ROW LEVEL SECURITY;
CREATE POLICY "用户只能看自己会话生成的名字"
    ON candidate_names
    FOR ALL
    USING (
        session_id IN (
            SELECT session_id FROM naming_sessions WHERE user_id = auth.uid()
        )
    );

-- conversation_messages：同上
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "用户只能看自己会话的消息"
    ON conversation_messages
    FOR ALL
    USING (
        session_id IN (
            SELECT session_id FROM naming_sessions WHERE user_id = auth.uid()
        )
    );

-- profiles：用户只能看/改自己的个人信息
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "用户只能操作自己的 profile"
    ON profiles
    FOR ALL
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());
