"""
【模块定位】入口层 - 命令行接口
【核心功能】argparse实现子命令，提供init-db/import-dataset/run-eval三大命令
【设计思想】工具化入口，无需改代码，通过命令完成所有操作，方便集成脚本与CI
"""
import argparse
import asyncio

from .db import init_db, SessionLocal, TestCase
from .config import load_config
from .data_io import import_dataset_jsonl
from .runner import run_batch
from .reporter import write_csv, write_html


def main():
    """CLI主入口函数"""
    # 创建顶层解析器
    parser = argparse.ArgumentParser(prog="eval_tool", description="LLM自动化评测工具")

    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # ---------- 子命令：init-db ----------
    subparsers.add_parser("init-db", help="初始化数据库")

    # ---------- 子命令：import-dataset ----------
    imp_parser = subparsers.add_parser("import-dataset", help="导入JSONL测试数据集")
    imp_parser.add_argument("--path", required=True, help="数据集文件路径")
    imp_parser.add_argument("--name", required=True, help="数据集名称")

    # ---------- 子命令：run-eval ----------
    run_parser = subparsers.add_parser("run-eval", help="执行评测")
    run_parser.add_argument("--ids", help="指定用例ID，逗号分隔")
    run_parser.add_argument("--all", action="store_true", help="执行全部用例")

    # 解析命令行参数
    args = parser.parse_args()
    # 加载配置
    cfg = load_config()

    # ---------- 处理init-db命令 ----------
    if args.cmd == "init-db":
        init_db()
        print("✅ 数据库初始化完成")
        return

    # ---------- 处理import-dataset命令 ----------
    if args.cmd == "import-dataset":
        count = import_dataset_jsonl(args.path, args.name)
        print(f"✅ 成功导入 {count} 条测试用例")
        return

    # ---------- 处理run-eval命令 ----------
    if args.cmd == "run-eval":
        session = SessionLocal()
        try:
            # 确定要执行的用例ID列表
            if args.all:
                # 查询全部用例
                tcs = session.query(TestCase).all()
                ids = [tc.id for tc in tcs]
            elif args.ids:
                # 逗号分割指定ID
                ids = [x.strip() for x in args.ids.split(",")]
            else:
                print("❌ 请指定 --all 或 --ids 参数")
                return
        finally:
            session.close()

        print(f"📋 共 {len(ids)} 条用例待执行")

        # 提取模型配置
        model_cfg = cfg.get("model", {})
        model_conf = {
            "name": model_cfg.get("name", "gpt-3.5-turbo"),
            "temperature": model_cfg.get("temperature", 0.0),
            "max_tokens": model_cfg.get("max_tokens", 512)
        }

        # 提取运行配置
        runner_cfg = cfg.get("runner", {})
        concurrency = runner_cfg.get("concurrency", 4)

        # 提取指标配置
        metrics_cfg = cfg.get("metrics", {})
        use_embedding = metrics_cfg.get("use_embedding", False)

        # 运行异步批量评测
        results = asyncio.run(
            run_batch(ids, model_conf, concurrency, use_embedding)
        )

        # 统计汇总
        total = len(results)
        pass_count = sum(1 for r in results if r["status"] == "pass")
        fail_count = total - pass_count
        pass_rate = f"{round(pass_count/total*100, 2)}%" if total else "0%"

        summary = {
            "total": total,
            "pass": pass_count,
            "fail": fail_count,
            "pass_rate": pass_rate
        }

        # 生成报告
        write_csv("results.csv", results)
        write_html("results.html", results, summary)

        print("\n📊 评测完成")
        print(f"总用例：{total} | 通过：{pass_count} | 失败：{fail_count} | 通过率：{pass_rate}")
        print("报告文件：results.csv / results.html")
        return


if __name__ == "__main__":
    main()
