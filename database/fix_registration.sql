-- =============================================================
-- 注册失败的修复SQL
-- 问题：auth.users 上的 INSERT 触发器执行失败，导致注册回滚
-- 修复：删除有问题的触发器，改为应用层懒创建
-- 使用方式：打开 Supabase 后台 → SQL Editor → 粘贴运行
-- =============================================================

-- 1. 删除 profile 触发器（profiles 表在代码中未使用）
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS handle_new_user();

-- 2. 删除余额触发器（余额已在 get_user_balance() 中懒创建）
DROP TRIGGER IF EXISTS on_auth_user_created_balance ON auth.users;
DROP FUNCTION IF EXISTS handle_new_user_balance();

-- 3. 创建 profiles 表（如果还不存在）
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    username TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================
-- 然后请运行完整的 supabase_schema.sql 建其他表
-- =============================================================
