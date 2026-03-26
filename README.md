# W4Agent — 基于智能体技术的Web无障碍检测系统

<p align="center">
  <img src="frontend/public/favicon.svg" width="80" alt="W4Agent Logo" />
</p>

<p align="center">
  <strong>将传统"规则驱动"的无障碍检测升级为"认知驱动"的智能化评估</strong>
</p>

<p align="center">
  <code>Python</code> · <code>FastAPI</code> · <code>LangChain</code> · <code>LangGraph</code> · <code>Playwright</code> · <code>React</code> · <code>Ant Design</code>
</p>

---

## 目录

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [四大核心模块](#四大核心模块)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 接口文档](#api-接口文档)
- [数据库设计](#数据库设计)
- [Agent 系统设计](#agent-系统设计)
- [无障碍检测规则](#无障碍检测规则)
- [前端工作台](#前端工作台)
- [开发指南](#开发指南)
- [部署方案](#部署方案)

---

## 项目简介

W4Agent 是一套新一代 Web 无障碍检测系统，针对当前自动化无障碍测试中存在的 **遍历策略僵化、动态适应能力弱、关键路径识别缺失** 等核心挑战，基于大语言模型（LLM）智能体技术研发而成。

### 核心理念

| 传统方案 | W4Agent |
|---------|---------|
| 规则驱动，逐条匹配 | 认知驱动，LLM 推理 + 规则引擎双轨 |
| 固定遍历策略 | 启发式自适应遍历，动态优先级排序 |
| 无法处理动态页面干扰 | 突发事件响应器实时处理弹窗/广告 |
| 脆弱的重复页面判断 | 语义嵌入 + 结构签名去重 |
| 单一工具执行 | 多 Agent 协作（规划-遍历-检测-报告） |
| 无历史经验复用 | 短期 + 长期记忆系统 |

### 检测标准

- **WCAG 2.1** (Web Content Accessibility Guidelines)
- **GB/T 37668-2019** 《信息技术 互联网内容无障碍可访问性技术要求与测试方法》

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端工作台 (React + Ant Design)              │
│  Dashboard │ 任务管理 │ 实时监控 │ 报告查看 │ 人工标注 │ 设置     │
└──────┬──────────────┬──────────────────────────────────────┘
       │ REST API     │ WebSocket
       ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                  后端服务层 (FastAPI)                           │
│  路由层 (api/v1/) │ 服务层 (services/) │ 数据层 (models/)       │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                   智能体引擎 (Agent Engine)                     │
│                                                              │
│  ┌───────────┐    LangGraph 状态机    ┌───────────────────┐  │
│  │ Master    │──── Plan ──→ Explore ──→│ Crawler Agent    │  │
│  │ Agent     │←────────────────────────│ (遍历决策)        │  │
│  │ (总控调度) │──── Plan ──→ Test ────→│ Detector Agent   │  │
│  │           │←────────────────────────│ (检测分析)        │  │
│  │           │──── Plan ──→ Report ──→│ Reporter Agent   │  │
│  └───────────┘                        │ (报告生成)        │  │
│       │                               └───────────────────┘  │
│       ▼                                                      │
│  ┌───────────────────────────────────────────────────���─────┐ │
│  │ 记忆系统: ShortTermMemory (会话内) + LongTermMemory (PG) │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│              自适应遍历器 (Adaptive Crawler)                    │
│                                                              │
│  Playwright 浏览器池 ──→ 页面分析器 (A11y Tree + DOM)         │
│       │                       │                              │
│       ▼                       ▼                              │
│  动作执行器 ◄──── 启发式策略 ◄──── 语义去重器                   │
│       │                       │                              │
│       ▼                       ▼                              │
│  状态图构建 ◄──── 突发事件响应器 (弹窗/广告/Cookie)             │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│              无障碍检测引擎 (Detection Engine)                  │
│                                                              │
│  规则引擎 (WCAG Rules)  ────→ 问题合并 ←──── AI 智能检测      │
│  · img-alt           · heading-order    · 视觉分析 (截图)     │
│  · img-alt-quality   · html-lang        · 语义分析 (alt质量)  │
│  · form-label        · landmark-structure · 交互分析 (键盘)   │
│  · link-text                                                 │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  PostgreSQL (pgvector)  │  Redis  │  文件存储 (截图/报告)      │
└──────────────────────────────────────────────────────────────┘
```

---

## 四大核心模块

### 1. 智能体引擎（Agent Engine）

> 目录：`backend/agent/`

集成大语言模型作为推理核心，基于 **LangGraph** 构建多 Agent 协作状态机。

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **Master Agent** | 任务分解、决策规划、调度协调 | 目标URL、当前进度 | 动作决策 (`EXPLORE`/`TEST`/`REPORT`/`COMPLETE`) |
| **Crawler Agent** | 页面探索决策、导航策略 | 当前页面状态、可交互元素 | 导航指令 (`navigate`/`click`/`skip`) |
| **Detector Agent** | AI 驱动的无障碍分析 | A11y 树、HTML、规则结果 | 补充问题列表 |
| **Reporter Agent** | 报告生成、摘要撰写 | 统计数据、问题分布 | 检测摘要 + 改进建议 |

**记忆机制：**
- **短期记忆（ShortTermMemory）**：会话内工作记忆，固定容量（100 条），存储当前任务的观察和决策
- **长期记忆（LongTermMemory）**：跨任务持久记忆，存入 PostgreSQL，包含情景记忆（检测经验）、语义记忆（模式知识）和程序记忆（处理策略）

**LLM 支持：**
- OpenAI GPT-4o / GPT-4
- Anthropic Claude
- 本地模型（通过 Ollama / vLLM）
- 通过 LangChain 抽象层自由切换

### 2. 自适应遍历器（Adaptive Crawler）

> 目录：`backend/crawler/`

| 组件 | 文件 | 功能 |
|------|------|------|
| **自适应遍历器** | `adaptive_crawler.py` | 主流程：导航→分析→发现链接→去重→存储 |
| **页面分析器** | `page_analyzer.py` | 提取 A11y 树、标题层级、图片、表单、链接、ARIA 地标 |
| **动作执行器** | `action_executor.py` | Playwright 浏览器池管理，封装导航/点击/填写/截图操作 |
| **启发式策略** | `heuristics.py` | 按 URL 模式评分排序（登录/表单页 +30 分，深度递减惩罚） |
| **语义去重器** | `deduplicator.py` | 内容哈希精确匹配 + 结构签名模板检测（同模板 ≥3 则跳过） |
| **状态图** | `state_graph.py` | 有向图记录页面发现/探索/测试状态及转换关系 |

**启发式优先级规则：**

| 类别 | URL 关键词 | 加分 |
|------|-----------|------|
| 高优先级 | login, signup, register, contact, form, checkout, search, settings | +30 |
| 中优先级 | about, faq, blog, product, service | +15 |
| 低优先级 | api, feed, sitemap, admin, static | -20 |

### 3. 突发事件响应器（Event Responder）

> 文件：`backend/crawler/event_responder.py`

实时监测并自动处理测试过程中出现的非预期界面元素：

| 事件类型 | 检测方式 | 处理策略 |
|---------|---------|---------|
| Cookie 同意横幅 | `[class*='cookie']`, `[class*='consent']`, `[class*='gdpr']` | 点击"接受/Accept/同意/OK" |
| 弹窗 / 模态框 | `[role='dialog']`, `.modal.show`, `[class*='popup']` | 点击"关闭/Close/×"或按 Escape |
| 广告遮罩 | `[class*='ad-overlay']`, `[class*='interstitial']` | 点击"跳过/Skip" |
| Alert 提示 | `[role='alert']` | 记录内容并尝试关闭 |

所有事件处理结果通过 WebSocket 实时通知前端。

### 4. 人机协同工作台

> 目录：`frontend/`

基于 React + Ant Design 构建的可视化前端界面：

| 页面 | 路由 | 功能 |
|------|------|------|
| 仪表盘 | `/` | 任务总览、统计卡片、最近任务列表 |
| 项目管理 | `/projects` | 项目 CRUD、关联任务 |
| 新建检测 | `/tasks/create` | 配置目标 URL、WCAG 级别、遍历深度等参数 |
| 任务详情 | `/tasks/:taskId` | 实时进度、问题列表、Agent 推理日志、任务配置 |
| 检测报告 | `/reports/:taskId` | 合规评分、问题统计、导出 HTML/PDF/JSON |
| 系统设置 | `/settings` | LLM 配置、Jira 集成 |

**实时通信**：通过 WebSocket 实时推送检测进度、页面发现、问题发现、Agent 推理过程。

---

## 技术栈

### 后端

| 类别 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | >= 0.115 |
| ORM | SQLAlchemy (async) | >= 2.0 |
| 数据库 | PostgreSQL (pgvector) | 16 |
| 缓存 | Redis | 7 |
| Agent 框架 | LangChain + LangGraph | >= 0.3 |
| LLM 接入 | langchain-openai, langchain-anthropic, langchain-community | >= 0.2 |
| 浏览器自动化 | Playwright | >= 1.47 |
| 数据库迁移 | Alembic | >= 1.13 |
| 报告生成 | Jinja2 + WeasyPrint | >= 3.1 / >= 62 |
| 认证 | python-jose (JWT) + passlib (bcrypt) | |
| 日志 | structlog | >= 24 |
| HTTP 客户端 | httpx | >= 0.27 |

### 前端

| 类别 | 技术 | 版本 |
|------|------|------|
| UI 框架 | React | ^18.3 |
| 组件库 | Ant Design | ^5.20 |
| 状态管理 | Zustand | ^4.5 |
| HTTP 客户端 | Axios | ^1.7 |
| 路由 | React Router DOM | ^6.26 |
| 构建工具 | Vite | ^5.4 |
| 语言 | TypeScript | ^5.5 |

### 基础设施

| 类别 | 技术 |
|------|------|
| 容器化 | Docker + Docker Compose |
| 数据库 | PostgreSQL 16 with pgvector |
| 缓存/消息 | Redis 7 |
| 反向代理 | Nginx (前端生产镜像内置) |

---

## 项目结构

```
W4Agent/
├── docker-compose.yml              # Docker 编排配置
├── Makefile                         # 常用命令快捷方式
├── .env.example                     # 环境变量模板
├── .gitignore
│
├── backend/                         # Python 后端
│   ├── Dockerfile
│   ├── pyproject.toml               # 依赖管理
│   ├── alembic.ini                  # 数据库迁移配置
│   │
│   ├── app/                         # FastAPI 应用层
│   │   ├── main.py                  # 应用入口 & 生命周期管理
│   │   ├── config.py                # 全局配置 (pydantic-settings)
│   │   ├── dependencies.py          # FastAPI 依赖注入
│   │   ├── api/
│   │   │   ├── v1/                  # REST API 路由
│   │   │   │   ├── router.py        # 路由聚合
│   │   │   │   ├── projects.py      # 项目管理
│   │   │   │   ├── tasks.py         # 任务管理 & 启停
│   │   │   │   ├── reports.py       # 报告查询 & 导出
│   │   │   │   ├── issues.py        # 问题管理
│   │   │   │   └── annotations.py   # 人工标注
│   │   │   └── ws/
│   │   │       └── task_monitor.py  # WebSocket 实时推送
│   │   ├── core/
│   │   │   ├── security.py          # JWT 认证
│   │   │   ├── exceptions.py        # 异常处理
│   │   │   └── logging.py           # 结构化日志
│   │   ├── db/
│   │   │   ├── session.py           # 异步数据库会话
│   │   │   └── redis.py             # Redis 客户端
│   │   ├── models/                  # SQLAlchemy ORM 模型
│   │   │   ├── base.py              # 基类 & Mixin
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── page.py
│   │   │   ├── issue.py
│   │   │   ├── report.py
│   │   │   ├── annotation.py
│   │   │   └── agent_memory.py
│   │   ├── schemas/                 # Pydantic 请求/响应模型
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── issue.py
│   │   │   ├── report.py
│   │   │   ├── annotation.py
│   │   │   ├── page.py
│   │   │   └── ws_message.py
│   │   └── services/                # 业务逻辑层
│   │       ├── task_service.py      # 任务生命周期 & Agent 启动
│   │       ├── report_service.py    # 报告生成 & 导出
│   │       ├── notification_service.py  # WebSocket 广播
│   │       └── jira_service.py      # Jira 集成
│   │
│   ├── agent/                       # 智能体引擎
│   │   ├── engine.py                # AgentEngine 入口
│   │   ├── orchestrator.py          # LangGraph 多 Agent 编排
│   │   ├── agents/
│   │   │   ├── base.py              # BaseAgent 抽象基类
│   │   │   ├── master_agent.py      # 主控 Agent
│   │   │   ├── crawler_agent.py     # 遍历 Agent
│   │   │   ├── detector_agent.py    # 检测 Agent
│   │   │   └── reporter_agent.py    # 报告 Agent
│   │   ├── llm/
│   │   │   └── provider.py          # LLM 工厂 (OpenAI/Claude/本地)
│   │   ├── memory/
│   │   │   ├── short_term.py        # 会话内短期记忆
│   │   │   └── long_term.py         # 跨任务长期记忆
│   │   ├── prompts/
│   │   │   ├── master.py            # 主控 Agent 提示词
│   │   │   ├── crawler.py           # 遍历 Agent 提示词
│   │   │   ├── detector.py          # 检测 Agent 提示词
│   │   │   └── reporter.py          # 报告 Agent 提示词
│   │   └── tools/
│   │       ├── a11y_tools.py        # 无障碍工具 (对比度/ARIA/标题)
│   │       └── browser_tools.py     # 浏览器操作工具
│   │
│   ├── crawler/                     # 自适应遍历器
│   │   ├── adaptive_crawler.py      # 遍历主逻辑
│   │   ├── page_analyzer.py         # 页面分析 (A11y Tree + DOM)
│   │   ├── action_executor.py       # Playwright 浏览器池 & 动作执行
│   │   ├── state_graph.py           # 应用状态图
│   │   ├── heuristics.py            # 启发式探索策略
│   │   ├── deduplicator.py          # 语义去重
│   │   └── event_responder.py       # 突发事件响应器
│   │
│   ├── detector/                    # 无障碍检测引擎
│   │   ├── detection_engine.py      # 检测调度 (规则 + AI)
│   │   ├── rule_based/
│   │   │   ├── rule_registry.py     # 规则注册表 & 基类
│   │   │   └── wcag_rules.py        # 7 条 WCAG 规则实现
│   │   └── ai_based/                # AI 检测（由 DetectorAgent 驱动）
│   │
│   ├── alembic/                     # 数据库迁移
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   └── tests/                       # 测试
│       └── conftest.py
│
└── frontend/                        # React 前端
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx                 # 应用入口
        ├── App.tsx                  # 路由配置
        ├── api/                     # API 客户端
        │   ├── client.ts            # Axios 实例 & 拦截器
        │   ├── projects.ts
        │   ├── tasks.ts
        │   ├── reports.ts
        │   └── ws.ts               # WebSocket 客户端
        ├── stores/                  # Zustand 状态管理
        │   ├── useProjectStore.ts
        │   └── useTaskStore.ts
        ├── pages/                   # 页面组件
        │   ├── Dashboard/
        │   ├── ProjectList/
        │   ├── TaskCreate/
        │   ├── TaskDetail/
        │   ├── ReportView/
        │   ├── Annotation/
        │   └── Settings/
        ├── components/
        │   └── Layout/AppLayout.tsx
        ├── types/                   # TypeScript 类型定义
        │   ├── project.ts
        │   ├── task.ts
        │   ├── report.ts
        │   ├── a11y.ts
        │   └── ws.ts
        └── styles/global.css
```

---

## 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd W4Agent

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM API Key

# 3. 启动所有服务
docker compose up -d

# 4. 访问
# 前端工作台: http://localhost:5173
# 后端 API:   http://localhost:8000/docs
```

### 方式二：本地开发

**前置要求：**
- Python >= 3.11
- Node.js >= 20
- PostgreSQL 16 (建议使用 pgvector 镜像)
- Redis 7

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 安装全部依赖
make install

# 3. 启动数据库（如果使用 Docker）
docker compose up -d postgres redis

# 4. 运行数据库迁移
make migrate

# 5. 启动后端（端口 8000）
make dev-backend

# 6. 启动前端（端口 5173，另开终端）
make dev-frontend
```

### 验证安装

```bash
# 后端健康检查
curl http://localhost:8000/docs

# 创建项目
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试项目","base_url":"https://example.com"}'

# 创建并启动检测任务
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project-id>","name":"首页检测","target_url":"https://example.com"}'
```

---

## 配置说明

所有配置通过 `.env` 文件管理，使用 `pydantic-settings` 自动加载。

### 应用配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_ENV` | 运行环境 | `development` |
| `DEBUG` | 调试模式 | `true` |

### 数据库配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://w4agent:w4agent_pass@localhost:5432/w4agent` |
| `DB_POOL_SIZE` | 连接池大小 | `20` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |

### LLM 配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 (`openai` / `claude` / `local`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | — |
| `OPENAI_MODEL` | OpenAI 模型名 | `gpt-4o` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | — |
| `ANTHROPIC_MODEL` | Anthropic 模型名 | `claude-sonnet-4-20250514` |
| `LOCAL_LLM_BASE_URL` | 本地模型地址 (Ollama) | `http://localhost:11434` |
| `LOCAL_LLM_MODEL` | 本地模型名 | `llama3` |

### 浏览器配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BROWSER_POOL_SIZE` | Playwright 浏览器池大小 | `3` |
| `PAGE_TIMEOUT_MS` | 页面加载超时（毫秒） | `30000` |
| `SCREENSHOT_DIR` | 截图存储路径 | `/tmp/w4agent/screenshots` |

### Jira 集成

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JIRA_BASE_URL` | Jira 实例地址 | — |
| `JIRA_API_TOKEN` | Jira API Token | — |
| `JIRA_PROJECT_KEY` | Jira 项目标识 | — |

### 安全配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | JWT 签名密钥 | `dev-secret-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `1440` |
| `CORS_ORIGINS` | 允许的跨域来源 | `["http://localhost:5173"]` |

---

## API 接口文档

后端启动后可访问自动生成的交互式文档：
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### REST API 概览

#### 项目管理 `/api/v1/projects`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/` | 创建项目 |
| `GET` | `/` | 项目列表（分页） |
| `GET` | `/{id}` | 获取项目详情 |
| `PATCH` | `/{id}` | 更新项目 |
| `DELETE` | `/{id}` | 删除项目 |

#### 检测任务 `/api/v1/tasks`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/` | 创建检测任务 |
| `GET` | `/` | 任务列表（支持按项目/状态筛选） |
| `GET` | `/{id}` | 获取任务详情 |
| `POST` | `/{id}/start` | 启动检测（后台运行 Agent Engine） |
| `POST` | `/{id}/stop` | 停止检测 |
| `DELETE` | `/{id}` | 删除任务 |

#### 问题管理 `/api/v1/issues`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 问题列表（支持按任务/严重程度/状态筛选） |
| `GET` | `/{id}` | 获取问题详情 |
| `PATCH` | `/{id}` | 更新问题状态/严重程度 |

#### 检测报告 `/api/v1/reports`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/task/{task_id}` | 获取任务报告 |
| `POST` | `/task/{task_id}/export` | 导出报告（HTML / PDF / JSON） |

#### 人工标注 `/api/v1/annotations`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/` | 创建标注（确认/误报/重分类/评论） |
| `GET` | `/issue/{issue_id}` | 获取问题的标注列表 |

### WebSocket 接口

| 路径 | 说明 |
|------|------|
| `ws://host/ws/task/{task_id}` | 实时任务监控 |

**推送消息类型：**

| type | 说明 | data 字段 |
|------|------|----------|
| `task_progress` | 任务进度 | `pages_discovered`, `pages_tested`, `issues_found`, `current_url` |
| `page_discovered` | 发现新页面 | `url`, `depth` |
| `issue_found` | 发现新问题 | 问题详情 |
| `agent_reasoning` | Agent 推理过程 | `agent`, `reasoning` |
| `event_detected` | 检测到突发事件 | `event_type`, `action_taken` |
| `task_completed` | 任务完成 | 最终统计 |
| `task_failed` | 任务失败 | `error` |

---

## 数据库设计

系统使用 PostgreSQL 存储结构化数据，共 7 张核心表。所有表均使用 UUID 主键和自动时间戳。

### ER 关系图

```
Project 1──N Task 1──N Page 1──N Issue 1──N Annotation
                  │                   │
                  └──1 Report         └── (检测到的无障碍问题)

AgentMemory (独立表，存储跨任务的 Agent 长期记忆)
```

### 表结构

#### projects — 项目

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `name` | VARCHAR(255) | 项目名称 |
| `description` | TEXT | 描述 |
| `base_url` | VARCHAR(2048) | 基础 URL |
| `owner` | VARCHAR(255) | 所有者 |
| `created_at` / `updated_at` | TIMESTAMPTZ | 时间戳 |

#### tasks — 检测任务

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `project_id` | UUID (FK) | 所属项目 |
| `name` | VARCHAR(255) | 任务名称 |
| `target_url` | VARCHAR(2048) | 检测目标 URL |
| `status` | ENUM | `pending` / `running` / `paused` / `completed` / `failed` / `cancelled` |
| `config` | JSON | 检测配置（深度、页数、WCAG 级别等） |
| `pages_discovered` | INTEGER | 已发现页面数 |
| `pages_tested` | INTEGER | 已检测页面数 |
| `issues_found` | INTEGER | 已发现问题数 |
| `error_message` | TEXT | 错误信息 |

#### pages — 页面

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `task_id` | UUID (FK) | 所属任务 |
| `url` | VARCHAR(2048) | 页面 URL |
| `title` | VARCHAR(512) | 页面标题 |
| `status` | ENUM | `discovered` / `crawling` / `testing` / `completed` / `failed` / `skipped` |
| `depth` | INTEGER | 遍历深度 |
| `content_hash` | VARCHAR(64) | 内容哈希（去重用） |
| `screenshot_path` | VARCHAR(512) | 截图路径 |
| `a11y_tree` | JSON | 可访问性树快照 |

#### issues — 无障碍问题

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `task_id` / `page_id` | UUID (FK) | 所属任务/页面 |
| `wcag_criterion` | VARCHAR(20) | WCAG 准则编号（如 `1.1.1`） |
| `wcag_level` | ENUM | `A` / `AA` / `AAA` |
| `rule_id` | VARCHAR(100) | 检测规则 ID |
| `severity` | ENUM | `critical` / `major` / `minor` / `info` |
| `status` | ENUM | `open` / `confirmed` / `false_positive` / `fixed` / `wont_fix` |
| `title` | VARCHAR(512) | 问题标题 |
| `description` | TEXT | 详细描述 |
| `recommendation` | TEXT | 修复建议 |
| `element_selector` | VARCHAR(1024) | 元素 CSS 选择器 |
| `element_html` | TEXT | 元素 HTML 片段 |
| `detected_by` | VARCHAR(50) | 检测来源（`rule` / `ai`） |
| `confidence` | FLOAT | AI 检测置信度 |
| `jira_issue_key` | VARCHAR(50) | 关联的 Jira 问题 |

#### reports — 检测报告

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `task_id` | UUID (FK, UNIQUE) | 一对一关联任务 |
| `overall_score` | FLOAT | 综合评分 (0-100) |
| `level_a_score` / `level_aa_score` / `level_aaa_score` | FLOAT | 分级合规评分 |
| `total_pages` / `total_issues` | INTEGER | 总计统计 |
| `critical_issues` / `major_issues` / `minor_issues` | INTEGER | 分类统计 |
| `summary` | TEXT | AI 生成的检测摘要 |
| `recommendations` | TEXT | AI 生成的改进建议 |
| `issue_breakdown` | JSON | 问题分类统计 |
| `html_path` / `pdf_path` / `json_path` | VARCHAR(512) | 导出文件路径 |

#### annotations — 人工标注

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `issue_id` | UUID (FK) | 关联问题 |
| `user_id` | VARCHAR(255) | 标注者 |
| `annotation_type` | ENUM | `confirm` / `false_positive` / `reclassify` / `comment` |
| `content` | TEXT | 标注内容 |
| `new_severity` | VARCHAR(20) | 重分类后的严重程度 |

#### agent_memories — Agent 长期记忆

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `memory_type` | ENUM | `episodic` / `semantic` / `procedural` |
| `domain` | VARCHAR(512) | 关联域名 |
| `key` | VARCHAR(512) | 记忆键 |
| `content` | TEXT | 记忆内容 |
| `metadata_json` | JSON | 元数据 |
| `relevance_score` | FLOAT | 相关性评分 |

---

## Agent 系统设计

### 多 Agent 协作架构

系统采用 **LangGraph 状态机** 编排四个专业化 Agent 的协作流程。

```
                    ┌────────────────────┐
                    │   初始状态          │
                    │ target_url, config │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
              ┌────►│    Plan (Master)   │◄────┐
              │     │  决策下一步动作     │     │
              │     └────────┬───────────┘     │
              │              │                  │
              │    ┌─────────┼─────────┐        │
              │    │         │         │        │
              │    ▼         ▼         ▼        │
              │ EXPLORE    TEST     REPORT   COMPLETE
              │    │         │         │        │
              │    ▼         ▼         ▼        ▼
              │ ┌──────┐ ┌──────┐ ┌──────┐  ┌─────┐
              └─┤Explore│ │ Test │ │Report│  │ END │
                │      │ │      │ │      │  └─────┘
                │Crawler│ │Detect│ │Report│
                │Agent  │ │Agent │ │Agent │
                └──────┘ └──────┘ └──────┘
```

### 执行流程

1. **Plan 阶段**：Master Agent 分析当前进度，决定执行 `EXPLORE`（探索新页面）、`TEST`（检测已发现页面）、`REPORT`（生成报告）或 `COMPLETE`（结束）
2. **Explore 阶段**：Crawler Agent 指导遍历器探索页面，发现新链接，构建状态图
3. **Test 阶段**：先运行规则引擎检测，再由 Detector Agent 进行 AI 补充分析
4. **Report 阶段**：Reporter Agent 基于统计数据生成摘要和改进建议
5. **循环**：Explore/Test 完成后回到 Plan，直到 Master 决定生成报告或达到迭代上限

### 安全机制

- **迭代上限**：`max_iterations` 防止无限循环（默认等于 `max_pages` 配置）
- **JSON 解析容错**：所有 Agent 的 LLM 输出解析均有 fallback 默认值
- **错误隔离**：单页探索或检测失败不影响整体流程

---

## 无障碍检测规则

### 内置规则（7 条）

| 规则 ID | WCAG 准则 | 级别 | 检测内容 | 严重程度 |
|---------|----------|------|---------|---------|
| `img-alt` | 1.1.1 非文本内容 | A | 图片是否有 `alt` 属性 | 严重 |
| `img-alt-quality` | 1.1.1 非文本内容 | A | `alt` 文本是否有意义（非 "image"/"图片" 等） | 重要 |
| `form-label` | 1.3.1 信息和关系 | A | 表单控件是否有关联 `<label>` 或 `aria-label` | 严重/重要 |
| `heading-order` | 1.3.1 信息和关系 | A | 标题层级是否连续、是否有 `<h1>` | 重要/一般 |
| `html-lang` | 3.1.1 页面语言 | A | `<html>` 是否有 `lang` 属性 | 严重 |
| `landmark-structure` | 1.3.1 信息和关系 | A | 页面是否有 `<main>` 和 `<nav>` 地标 | 重要/一般 |
| `link-text` | 2.4.4 链接目的 | A | 链接是否有可识别文本（非 "点击这里"/"更多"） | 严重/一般 |

### AI 补充检测

Detector Agent 在规则引擎之后运行，重点分析：

1. **alt 文本语义质量**：alt 是否真正描述了图片内容（而非仅"存在"）
2. **ARIA 属性正确性**：角色与属性是否配对正确
3. **表单标签清晰度**：标签是否清晰表达了输入目的
4. **页面结构逻辑性**：标题、地标、区域划分是否合理
5. **视觉可辨识性**：颜色对比度、按钮可识别性（通过截图分析）

### 扩展规则

实现自定义规则只需继承 `A11yRule` 并注册：

```python
from detector.rule_based.rule_registry import A11yRule, registry

class MyCustomRule(A11yRule):
    rule_id = "my-rule"
    wcag_criterion = "2.1.1"
    wcag_level = "A"
    description = "Custom rule description"

    def check(self, page_data: dict) -> list[dict]:
        issues = []
        # 检测逻辑
        return issues

registry.register(MyCustomRule())
```

---

## 前端工作台

### 页面说明

#### 仪表盘 (`/`)

展示全局统计卡片（总任务数、已完成、问题数、页面数）和最近任务列表。支持快速跳转到任务详情或报告。

#### 项目管理 (`/projects`)

项目的 CRUD 管理界面，每个项目关联一个基础 URL，可创建多个检测任务。

#### 新建检测 (`/tasks/create`)

配置项：
- 所属项目、任务名称、目标 URL
- WCAG 级别（A / AA / AAA）
- 最大遍历深度和页面数
- 视口尺寸
- AI 检测和截图开关
- 是否立即执行

#### 任务详情 (`/tasks/:taskId`)

三栏式布局：
1. **进度面板**：实时更新的发现页面、已检测页面、问题数量
2. **问题列表 Tab**：按严重程度标签化显示，支持筛选
3. **Agent 日志 Tab**：时间线形式展示 Agent 的实时推理过程
4. **配置 Tab**：当前任务的检测参数

支持启动/停止操作，通过 WebSocket 接收实时更新。

#### 检测报告 (`/reports/:taskId`)

- 环形图展示综合评分（绿色 ≥80 / 黄色 ≥60 / 红色 <60）
- WCAG A/AA 分级合规度
- 问题分类统计（严重/重要/一般）
- 详细问题表格（支持按严重程度筛选）
- 一键导出 HTML / PDF / JSON

#### 系统设置 (`/settings`)

LLM 提供商和 API Key 配置、Jira 集成配置。

---

## 开发指南

### Makefile 命令

```bash
make help          # 查看所有可用命令
make install       # 安装全部依赖
make dev-backend   # 启动后端开发服务器 (localhost:8000)
make dev-frontend  # 启动前端开发服务器 (localhost:5173)
make dev           # 同时启动前后端
make test          # 运行后端测试
make test-cov      # 运行测试并生成覆盖率报告
make lint          # 代码检查
make format        # 代码格式化
make migrate       # 运行数据库迁移
make migrate-create msg="描述"  # 创建新迁移
```

### 数据库迁移

```bash
# 创建迁移脚本
cd backend
alembic revision --autogenerate -m "add new column"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 添加新的 API 端点

1. 在 `app/schemas/` 创建请求/响应模型
2. 在 `app/api/v1/` 创建路由模块
3. 在 `app/api/v1/router.py` 注册路由
4. 如需业务逻辑，在 `app/services/` 添加服务

### 添加新的 Agent

1. 在 `agent/prompts/` 定义提示词
2. 在 `agent/agents/` 继承 `BaseAgent` 实现新 Agent
3. 在 `agent/orchestrator.py` 的状态图中集成

---

## 部署方案

### Docker Compose（推荐）

```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止
docker compose down

# 清除数据（谨慎）
docker compose down -v
```

**服务清单：**

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | 数据库（含 pgvector 向量扩展） |
| `redis` | `redis:7-alpine` | 6379 | 缓存和消息 |
| `backend` | 自构建 | 8000 | FastAPI 后端 |
| `frontend` | 自构建 | 5173→80 | React 前端（Nginx 提供） |

### 生产环境注意事项

1. **修改 SECRET_KEY**：务必替换默认的 JWT 密钥
2. **配置 CORS_ORIGINS**：限制为实际域名
3. **关闭 DEBUG**：设置 `DEBUG=false`
4. **LLM API Key**：妥善保管，不要提交到代码仓库
5. **PostgreSQL**：配置持久化存储卷和备份策略
6. **Playwright**：生产环境确保 Chromium 依赖已安装

---

## 许可证

本项目仅供学术研究和教学使用。
