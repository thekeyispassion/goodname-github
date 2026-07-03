一、大语言模型取名系统的调研（取一个名字需要关注什么方面）
1. 基础信息类 姓氏 性别 名字字数
2. 出生信息类 出生日期 出生时辰 出生地点
3. 命理与传统文化类 生辰八字 五行偏好 生肖属相 字辈/族谱 三才五格
4. 寓意与风格偏好类 寓意方向 取名风格 典籍来源偏好 诗词典故 星座特质
5. 避讳与限制类 避讳字 避讳人名 禁用字 避免重名
6. 家庭与社会信息类 父亲姓名 母亲姓名 祖上姓名

二、业务流程
整体以双区域交互形式展开，用户打开取名网页后，左侧独立信息采集面板展开，供用户填写姓氏、性别、字数、出生日期等基础信息，并选择是否有其他需求——若选择“无”，直接点击确定即可；若选择“有”，面板动态展开四类补充信息区域（命理与传统文化、寓意与风格偏好、避讳与限制、家庭与社会信息），填写完成后点击确定。用户点击确定后，信息采集面板向左滑入页面左侧的隐藏栏中，主区域同步展开为智能体对话框，系统自动生成候选名字及寓意解析。后续用户可在对话框中提出修改意见，系统结合上下文记忆进行多轮优化调整，反复迭代直至用户满意结束对话；对话过程中，用户亦可随时点击左侧隐藏栏展开采集面板，查看或修改初始信息。

```mermaid
graph TD
    %% 定义样式
    classDef userAction fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef aiProcess fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef endNode fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px;
    classDef layout fill:#e8eaf6,stroke:#283593,stroke-width:2px,stroke-dasharray:5 5;

    Start([用户打开取名网页]) --> Panel[显示独立信息采集面板]
    Panel --> Step1["用户填写基础信息<br>姓氏/性别/字数/出生日期/时辰"]
    Step1:::userAction --> Check{是否有<br>其他需求?}:::decision

    Check -- 否 --> Submit1[用户点击确定]:::userAction
    Check -- 是 --> Step2["用户填写四类补充信息<br>1.命理与传统文化<br>2.寓意与风格偏好<br>3.避讳与限制<br>4.家庭与社会信息"]:::userAction
    Step2 --> Submit2[用户点击确定]:::userAction

    Submit1 --> Slide["信息采集面板左滑<br>进入左侧隐藏栏"]:::layout
    Submit2 --> Slide

    Slide --> Dialog[主区域展开<br>智能体对话框]:::aiProcess
    Dialog --> Gen1[智能体生成候选名字及寓意]:::aiProcess

    Gen1 --> Feedback{用户是否<br>提出修改意见?}:::decision

    Feedback -- 是 --> Modify["智能体根据意见优化调整<br>给出修改结果"]:::aiProcess
    Modify --> Feedback

    Feedback -- 否 --> End([结束对话 / 用户满意离开]):::endNode

    %% 用户可随时点击隐藏栏展开面板查看/修改采集信息
    Dialog -.->|点击隐藏栏图标<br>可查看/修改采集信息| Panel
```

三、UI界面
整体界面采用“左侧信息采集面板 + 右侧智能体对话框”的双区域布局设计，用户打开网页后，左侧独立的采集面板展开显示，清晰分区呈现基础信息输入区（姓氏、性别、字数、出生日期、时辰）和可动态展开的补充信息区（命理与文化、寓意风格、避讳限制、家庭社会信息），所有表单项均配有明确的标签和示例占位符，底部为突出的“确定/开始取名”按钮；右侧主区域初始展示引导语，待用户点击确定后，左侧面板向左平滑滑入窄条隐藏栏（仅保留“☰ 信息采集”图标），主区域无缝切换为对话界面，自上而下依次展示智能体头像与消息气泡（含候选名字卡片及字义、音韵、出处等详细解析）、用户反馈消息气泡，以及底部固定的文本输入框和发送按钮，整体采用新中式极简风格，以暖白背景搭配朱砂红与淡金点缀，兼顾文化温度与清晰的信息层级。

渲染图![AI图像生成工具介绍](D:/software/typora/image/goodname/AI图像生成工具介绍.png)

四、技术方案



设计流程

```mermaid
graph TD
    A[1. 技术选型] --> B["2. 数据流设计（系统架构图）"]
    B --> C[3. 数据库设计]
    B --> D[4. 提示词设计]
    C --> E[5. 核心模块设计]
    D --> E
    E --> F[6. 项目目录结构设计]
    
    A -.->|约束| C
    A -.->|约束| E
    B -.->|实体来源| C
    B -.->|输入/输出| D
    E -.->|组织形式| F
```







1.技术选型（选择什么技术）

| 技术层级         | 我的最终选型                 | 决策依据                                                     |
| :--------------- | :--------------------------- | :----------------------------------------------------------- |
| **开发语言**     | **Python 3.9+**              | 语法简洁，大模型生态（AI库）最成熟，项目代码量少，适合快速迭代。 |
| **前端界面**     | **Streamlit**                | **关键决策**：纯Python生成网页，无需学前端三件套。自带侧边栏(`st.sidebar`)和聊天组件(`st.chat_input`)，完美对应“左面板+右对话”设计。 |
| **大语言模型**   | **DeepSeek API**（在线）     | 注册即送500万tokens免费额度；中文取名逻辑稳定；API调用仅需3行代码。**不选本地模型**：因为需GPU显存≥6GB，学生电脑跑不动。 |
| **本地数据库**   | **SQLite**                   | Python内置`sqlite3`模块，**零配置、零安装**，一个文件就是一个库。适合项目初期练手SQL语句。 |
| **云数据库**     | **Supabase**                 | 老师明确推荐。提供免费500MB空间，带可视化后台管理界面，无需自己搭建云服务器。 |
| **会话状态管理** | **st.session_state**（内存） | Streamlit内置功能，一行代码存数据，不用额外安装Redis。项目关闭数据自动释放，足够MVP演示。 |
| **代码管理**     | **Git + GitHub**             | 防代码丢失，便于展示版本迭代过程（课程报告可截图提交记录）。 |

2.（这些技术怎么搭配干活）

​		1.数据流
（精简版）

```mermaid
graph TB
    subgraph UI["用户界面层"]
        Form["📝 表单数据<br>姓氏/性别/出生日期/偏好"]
        Input["💬 修改意见<br>多轮对话输入"]
        Display["🖥️ 名字展示<br>候选名+寓意+音韵"]
    end

    subgraph APP["应用逻辑层"]
        Builder["🔧 提示词组装器<br>将表单+历史拼接为提示词"]
        Parser["📋 结果解析器<br>从JSON中提取名字列表"]
        Memory["💾 会话记忆<br>st.session_state"]
    end

    subgraph LLM["大模型层"]
        API["🤖 DeepSeek API<br>输入: 提示词<br>输出: JSON名字列表"]
    end

    subgraph DB["数据存储层"]
        SQLite["💾 SQLite<br>本地记录"]
        Supabase["☁️ Supabase<br>云端同步"]
    end

    Form -->|点击确定| Builder
    Input -->|发送消息| Builder
    Builder -->|完整提示词| API
    API -->|JSON字符串| Parser
    Parser -->|解析后的列表| Memory
    Memory -->|渲染| Display
    Display -->|用户看后提意见| Input
    Parser -.->|异步保存| SQLite
    Parser -.->|异步保存| Supabase
    Memory -->|对话历史| Builder
```

（详细版）

```mermaid
sequenceDiagram
    participant U as 用户
    participant S as Streamlit UI
    participant SS as st.session_state
    participant PB as PromptBuilder
    participant LLM as DeepSeek API
    participant DB as SQLite/Supabase

    U->>S: 1. 填写表单并点击“确定”
    S->>SS: 2. 保存表单数据至 user_input
    SS->>PB: 3. 调用 build_generate_prompt(user_input)
    PB->>PB: 4. 加载system_prompt + 拼接用户信息 + JSON约束
    PB-->>LLM: 5. 发送完整消息列表
    LLM-->>S: 6. 返回JSON字符串（含5个名字及解析）
    S->>S: 7. result_parser解析为Python列表
    S->>SS: 8. 存入 st.session_state.names
    S->>DB: 9. 异步保存至SQLite（本地）+ Supabase（云端）
    S-->>U: 10. 渲染候选名字卡片（右侧对话框）

    U->>S: 11. 在底部输入框输入修改意见
    S->>SS: 12. 将用户消息追加至 messages
    SS->>PB: 13. 调用 build_refine_prompt(messages, user_input)
    PB->>PB: 14. 拼接完整对话历史 + 原始需求
    PB-->>LLM: 15. 发送迭代优化请求
    LLM-->>S: 16. 返回优化后的新名字列表
    S->>SS: 17. 更新 st.session_state.names
    S-->>U: 18. 渲染更新后的名字卡片，对话继续
```

3.数据库设计（难度1）

本项目的数据库设计已从初步的3张表方案（NAMING_RECORDS + CHARACTER_USAGE + CLOUD_SYNC）
完善为更适合难度1~3的分表方案。

**难度1** 只需要3张核心表：

| 表名 | 作用 |
|:---|:---|
| `naming_sessions` | 记录每次取名会话的用户输入信息 |
| `candidate_names` | 记录AI生成的每个候选名字及解析 |
| `conversation_messages` | 记录用户和AI的多轮对话历史 |

详细的表结构、字段说明、DDL语句、Python操作代码 → 见 **[技术方案.md](./技术方案.md#二数据库设计)**

难度2/3需要的用户表、计费表等也在技术方案.md中有完整设计（后续扩展时使用）。