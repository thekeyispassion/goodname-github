-- =============================================================
-- 关闭 name_evaluations 表的 RLS
-- 使用方式：Supabase 后台 → SQL Editor → 粘贴运行
-- =============================================================

-- 删除策略
DROP POLICY IF EXISTS "用户只能操作自己的评价记录" ON name_evaluations;

-- 关闭 RLS
ALTER TABLE name_evaluations DISABLE ROW LEVEL SECURITY;
