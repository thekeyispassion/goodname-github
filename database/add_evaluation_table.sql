-- =============================================================
-- AI评价名字功能 - 数据库迁移
-- 使用方式：Supabase 后台 → SQL Editor → 粘贴运行
-- =============================================================

-- 新建评价记录表
CREATE TABLE IF NOT EXISTS name_evaluations (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    name_text TEXT NOT NULL,
    meaning_score INTEGER DEFAULT 0,
    sound_score INTEGER DEFAULT 0,
    culture_score INTEGER DEFAULT 0,
    wuxing_score INTEGER DEFAULT 0,
    overall_score INTEGER DEFAULT 0,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 策略（幂等：先删后建）
ALTER TABLE name_evaluations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "用户只能操作自己的评价记录" ON name_evaluations;
CREATE POLICY "用户只能操作自己的评价记录"
    ON name_evaluations
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
