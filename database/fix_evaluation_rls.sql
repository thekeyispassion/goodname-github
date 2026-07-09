-- =============================================================
-- AI评价名字功能 - RLS 修复（表已存在时用）
-- 使用方式：Supabase 后台 → SQL Editor → 粘贴运行
-- =============================================================

ALTER TABLE name_evaluations ENABLE ROW LEVEL SECURITY;

-- 如果策略已存在，先删后建
DROP POLICY IF EXISTS "用户只能操作自己的评价记录" ON name_evaluations;

CREATE POLICY "用户只能操作自己的评价记录"
    ON name_evaluations
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- =============================================================
-- 验证策略是否生效
-- =============================================================
SELECT tablename, policyname
FROM pg_policies
WHERE tablename = 'name_evaluations';
-- 预期输出：一行，policyname = "用户只能操作自己的评价记录"
