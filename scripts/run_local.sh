#!/usr/bin/env bash
# 本地一键演示脚本：按顺序执行初始化→导入数据→运行评测→生成报告
set -e  # 遇到错误立即停止，避免错误累积

echo "===== 步骤1：初始化数据库 ====="
python -m src.eval_tool.cli init-db

echo ""
echo "===== 步骤2：导入示例测试数据集 ====="
python -m src.eval_tool.cli import-dataset --path data/examples_eval.jsonl --name demo

echo ""
echo "===== 步骤3：执行全部用例评测 ====="
python -m src.eval_tool.cli run-eval --all

echo ""
echo "===== 执行完成 ====="
echo "报告文件：results.csv / results.html"
