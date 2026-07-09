-- =============================================================
-- 评价名字与打分功能 - 数据库迁移
-- 使用方式：Supabase 后台 → SQL Editor → 粘贴运行
-- =============================================================

-- 在 candidate_names 表新增用户评分和备注字段
ALTER TABLE candidate_names ADD COLUMN IF NOT EXISTS user_rating INTEGER;
ALTER TABLE candidate_names ADD COLUMN IF NOT EXISTS user_note TEXT;

-- 验证字段已添加
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'candidate_names'
  AND column_name IN ('user_rating', 'user_note');
