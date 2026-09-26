"""
eval_tool 包初始化文件
本包为LLM自动化评测工具的核心实现，按分层架构划分为：
- 配置层：config
- 数据层：db、data_io
- 能力层：prompt_engine
- 适配层：adapters
- 调度层：runner
- 评测层：metrics
- 输出层：reporter
- 流程层：testcase_gen、bug_tracker
- 工具层：utils
"""
