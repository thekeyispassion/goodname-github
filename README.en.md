# GoodName - AI Chinese Name Generator

> Software Outsourcing Practice Base — Freshman Training Project
>
> An intelligent Chinese naming system built with DeepSeek AI + Streamlit + Supabase, supporting multi-turn refinement, AI name evaluation, history management, and rating filters.

## Features

- **🤖 AI Naming** — Enter surname, gender, birth info, AI generates 5 candidate names with meanings, phonetics, cultural references, and scores
- **🔄 Multi-turn Refinement** — Provide feedback to refine names, AI adjusts with conversation context
- **📝 AI Evaluation** — Input any name for five-dimension scoring (meaning, sound, culture, wuxing, overall)
- **⭐ User Rating** — Rate names with stars + notes, filter history by rating
- **📋 History** — Search, favorite, and rate-filter past naming sessions
- **💰 Credit System** — Each generation/evaluation costs 1 credit, simulated top-up supported
- **🔐 Auth** — Supabase email + password login with "Remember Me"

## Tech Stack

| Layer | Technology |
|:---|:---|
| Frontend | Streamlit 1.58 |
| AI | DeepSeek API |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth |
| Language | Python 3.9+ |

## Project Structure

```
goodname/
├── app.py                         # Login/Register + route guard
├── pages/
│   ├── 1_取名主页.py               # AI naming
│   ├── 2_AI评价名字.py             # AI evaluation
│   ├── 3_历史记录.py               # History (search/favorite/rating)
│   └── 4_个人中心.py               # Profile (balance/top-up/password)
├── ui/
│   ├── theme.py                   # Theme + navbar + error helper
│   ├── login_page.py              # Login form
│   ├── register_page.py           # Register form
│   ├── sidebar.py                 # Info collection panel
│   └── chat_area.py               # Chat area + name cards + ratings
├── database/
│   ├── init.py                    # Supabase connection
│   ├── operations.py              # All DB operations
│   ├── supabase_schema.sql        # Table creation
│   ├── fix_registration.sql       # Registration fix
│   ├── add_rating_columns.sql     # Rating fields migration
│   ├── add_evaluation_table.sql   # Evaluation table migration
│   └── disable_evaluation_rls.sql # Disable RLS on evaluation table
├── llm/
│   ├── client.py                  # DeepSeek API
│   └── prompt_builder.py         # Prompts (naming/refine/evaluate)
├── utils/
│   └── parser.py                  # JSON parser
├── goodname-v2.0.md               # Requirements doc
├── 技术方案.md                     # Technical design
├── 项目流程图.md                   # Architecture + flows
├── 开发记录.md                     # Development log
├── CLAUDE.md                      # Project rules
├── requirements.txt               # Python dependencies
├── .env.example                   # Env template
└── .gitignore
```

## Quick Start

### 1. Setup Environment

```bash
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
DEEPSEEK_API_KEY=sk-your-key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
```

### 3. Initialize Database

Run the following SQL files in Supabase SQL Editor:
1. `database/supabase_schema.sql` — Create tables
2. `database/add_rating_columns.sql` — Rating fields
3. `database/add_evaluation_table.sql` — Evaluation table
4. `database/disable_evaluation_rls.sql` — Disable RLS on evaluation table

### 4. Run

```bash
streamlit run app.py
```

### 5. Dev Mode

Set `DEV_MODE=true` in `.env` to skip login during development.

## Documentation

| Document | Description |
|:---|:---|
| `goodname-v2.0.md` | Requirements (flow charts, UI design) |
| `技术方案.md` | Technical design (database, module design) |
| `项目流程图.md` | System architecture, pages, business flows |
| `开发记录.md` | Development log (Vibe Coding deliverables) |
| `安装部署手册.md` | Setup guide: env, Supabase, DeepSeek, deployment |
| `用户操作手册.md` | User manual: register, naming, evaluation, history |
| `CLAUDE.md` | Project rules |
