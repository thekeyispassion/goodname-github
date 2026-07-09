# 智能取名系统 (GoodName)

> 软件外包实践基地 —— 新生实训项目
> 
> 基于 DeepSeek AI + Streamlit + Supabase 的智能中文取名系统，支持多轮对话优化、AI评价名字、历史管理与评分筛选。

## 功能特性

- **🤖 AI 智能取名** — 输入姓氏、性别、出生信息，AI 生成 5 个候选名字（含字义、音韵、出处、五行、评分）
- **🔄 多轮修改** — 对不满意的结果提出修改意见，AI 结合上下文重新生成
- **📝 AI 评价名字** — 输入任意名字，AI 从字义/音韵/文化/五行/寓意五个维度评分
- **⭐ 用户打分** — 对候选名字打星评分 + 备注，历史记录支持评分筛选
- **📋 历史记录** — 取名历史可搜索、收藏、评分筛选
- **💰 余额计费** — 每次生成/评价消耗 1 次，支持模拟充值
- **🔐 登录注册** — Supabase Auth 邮箱 + 密码，支持"记住我"

## 技术栈

| 层级 | 技术 |
|:---|:---|
| 前端 | Streamlit 1.58 |
| AI | DeepSeek API |
| 数据库 | Supabase (PostgreSQL) |
| 认证 | Supabase Auth |
| 语言 | Python 3.9+ |

## 项目结构

```
goodname/
├── app.py                         # 登录/注册入口 + 路由守卫
├── pages/
│   ├── 1_取名主页.py               # AI 智能取名
│   ├── 2_AI评价名字.py             # AI 单名评价
│   ├── 3_历史记录.py               # 历史搜索/收藏/评分筛选
│   └── 4_个人中心.py               # 余额/充值/密码/注销/消费记录
├── ui/
│   ├── theme.py                   # 全局主题 + 导航栏 + 错误提示
│   ├── login_page.py              # 登录表单
│   ├── register_page.py           # 注册表单
│   ├── sidebar.py                 # 信息采集面板
│   └── chat_area.py               # 对话区 + 名字卡片 + 评分
├── database/
│   ├── init.py                    # Supabase 连接
│   ├── operations.py              # 全部数据库操作
│   ├── supabase_schema.sql        # 建表语句
│   ├── fix_registration.sql       # 注册修复
│   ├── add_rating_columns.sql     # 评分字段迁移
│   ├── add_evaluation_table.sql   # 评价表迁移
│   └── disable_evaluation_rls.sql # 关闭评价表 RLS
├── llm/
│   ├── client.py                  # DeepSeek API
│   └── prompt_builder.py         # 提示词（取名+修改+评价）
├── utils/
│   └── parser.py                  # JSON 结果解析
├── goodname-v2.0.md               # 需求文档
├── 技术方案.md                     # 技术设计
├── 项目流程图.md                   # 架构+业务流程图
├── 开发记录.md                     # 开发过程记录
├── CLAUDE.md                      # 项目规则
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量模板
└── .gitignore
```

## 快速开始

### 1. 环境准备

```bash
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的密钥：

```env
DEEPSEEK_API_KEY=sk-your-key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
```

### 3. 初始化数据库

在 Supabase SQL Editor 中依次运行：
1. `database/supabase_schema.sql` — 建表
2. `database/add_rating_columns.sql` — 评分字段
3. `database/add_evaluation_table.sql` — 评价表
4. `database/disable_evaluation_rls.sql` — 关闭评价表 RLS

### 4. 启动

```bash
streamlit run app.py
```

### 5. 开发模式

在 `.env` 中设置 `DEV_MODE=true` 可跳过登录直接进入取名主页。

## 文档

| 文档 | 说明 |
|:---|:---|
| `goodname-v2.0.md` | 需求文档（含业务流程图、UI设计） |
| `技术方案.md` | 技术设计文档（数据库、模块设计） |
| `项目流程图.md` | 系统架构图、页面路由、业务流程 |
| `开发记录.md` | 开发过程记录（Vibe Coding 交付物） |
| `安装部署手册.md` | 环境配置、Supabase/DeepSeek 配置、启动部署 |
| `用户操作手册.md` | 注册登录、取名、AI评价、历史记录、个人中心 |
| `CLAUDE.md` | 项目规则 |
