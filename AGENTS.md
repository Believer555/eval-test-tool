# AGENTS.md

This file provides guidance to Lingma (lingma.aliyun.com) when working with code in this repository.

## Project Overview

轻量化 LLM 自动化评测工具（eval-test-tool）。融合传统软件测试全流程，覆盖需求管理、用例设计、批量执行、多维度断言、缺陷跟踪、回归验证完整链路。

## Build & Run Commands

```bash
# 激活虚拟环境
.venv\Scripts\activate          # Windows PowerShell

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（首次使用必须执行）
python -m src.eval_tool.cli init-db

# 导入 JSONL 测试数据集
python -m src.eval_tool.cli import-dataset --path data/examples_eval.jsonl --name demo

# 执行全部用例评测
python -m src.eval_tool.cli run-eval --all

# 执行指定用例（逗号分隔 ID）
python -m src.eval_tool.cli run-eval --ids tc001,tc002

# 本地一键演示（bash）
bash scripts/run_local.sh
```

评测完成后生成 `results.csv` 和 `results.html` 报告文件。

## Environment Variables

- `OPENAI_API_KEY` — OpenAI API 密钥，模型调用必需
- `GITHUB_TOKEN` — GitHub Issue 自动创建缺陷单时使用
- `EVAL_TOOL_DB` — 可选，自定义 SQLite 数据库文件路径（默认 `data/eval_tool.db`）

## Architecture

### Data Pipeline

```
Requirement → TestCase → TestRun → Bug
```

全链路可追溯。核心数据流：导入 JSONL 数据集 → 存入 SQLite → 异步并发调用 LLM → 多维度评测 → 持久化结果 → 生成报告。

### Module Responsibilities

| 模块 | 文件 | 职责 |
|------|------|------|
| CLI 入口 | `cli.py` | argparse 子命令分发：`init-db` / `import-dataset` / `run-eval` |
| 配置管理 | `config.py` | 读取 `configs/default.yaml`，返回配置字典 |
| ORM 持久化 | `db.py` | SQLAlchemy 定义四个实体：`Requirement` / `TestCase` / `TestRun` / `Bug`，SQLite 存储 |
| 数据导入 | `data_io.py` | JSONL 读取与 TestCase 入库，`merge` 语义防重复 |
| 并发运行器 | `runner.py` | 异步批量执行，`asyncio.Semaphore` 控制并发数，同步模型调用通过 `run_in_executor` 包装 |
| 评测指标 | `metrics.py` | 三级指标：`exact_match`（精确匹配）→ `ratio_score`（difflib 文本相似度）→ `embedding_score`（sentence-transformers 语义相似度，按需开启） |
| 模型适配器 | `adapters/openai_adapter.py` | 封装 OpenAI SDK，统一返回 `{text, raw, latency_ms, tokens}` |
| Prompt 引擎 | `prompt_engine.py` | Jinja2 模板渲染，模板文件在 `templates/prompt/` |
| 报告生成 | `reporter.py` | CSV / JSON / HTML 多格式输出，HTML 使用 `templates/report/template.html.j2` |
| 缺陷跟踪 | `bug_tracker.py` | 调用 GitHub API 创建 Issue |
| 用例生成 | `testcase_gen.py` | 输入需求文本，调用 LLM 自动生成测试用例草稿 |

### Adapter Pattern

所有模型适配器遵循统一接口契约，返回 `{text, latency_ms, tokens, raw}` 结构。新增模型提供方时，在 `adapters/` 下添加新适配器即可，`runner.py` 中切换调用目标。

### Key Design Decisions

- **配置驱动**：所有可变参数集中在 `configs/default.yaml`，代码与配置完全分离
- **并发模型**：`runner.py` 使用 `asyncio` + `Semaphore` 限流，同步的 OpenAI SDK 调用通过 `loop.run_in_executor` 放入线程池，避免阻塞事件循环
- **语义相似度懒加载**：`metrics.py` 中 `SentenceTransformer` 模型仅在 `use_embedding=true` 时首次加载
- **pass/fail 判定**：当前以 `exact_match` 为唯一判定标准（见 `runner.py` 第 60 行）
- **数据库可替换**：ORM 层抽象，当前使用 SQLite，可通过修改 `db.py` 中 engine 配置切换

## Data Format

JSONL 测试数据集每行格式：

```json
{"id": "tc001", "input": "问题文本", "reference": "期望答案"}
```

`id` 字段可选，缺失时自动生成 `{dataset_name}-{uuid}` 前缀的 ID。

## Configuration

`configs/default.yaml` 主要配置项：

- `model`：provider / name / temperature / max_tokens
- `runner`：concurrency（并发数）、rate_limit_qps
- `metrics`：use_embedding（是否启用语义相似度）、embedding_model
- `report`：formats（输出格式列表）
- `bug`：auto_open、github_repo、github_token_env
- `regression`：golden_dir（金标准基线目录）
