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
-- 注意：此表不用触发器，由应用层懒创建
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    username TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

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

-- =============================================================
-- v2.0 新增表：余额/充值/消费
-- =============================================================

-- 5. 用户余额表
CREATE TABLE IF NOT EXISTS user_balances (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    balance INTEGER DEFAULT 0,
    total_recharged INTEGER DEFAULT 0,
    total_consumed INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. 充值记录表
CREATE TABLE IF NOT EXISTS recharge_records (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    amount INTEGER NOT NULL,
    money DECIMAL(10,2) NOT NULL,
    payment_method TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. 消费记录表
CREATE TABLE IF NOT EXISTS consumption_records (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    session_id TEXT REFERENCES naming_sessions(session_id),
    amount INTEGER NOT NULL,
    consumption_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 注：余额不设触发器，由 get_user_balance() 懒创建（新用户首次查询时自动送20次）
